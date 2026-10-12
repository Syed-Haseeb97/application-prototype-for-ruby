"""Second launches must reach the running instance (offscreen Qt)."""
import os
import threading
import unittest
import uuid

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication

from core.single_instance import SingleInstance


class SingleInstanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.key = f"ruby-test-{uuid.uuid4().hex}"
        self.instances = []

    def tearDown(self):
        for inst in self.instances:
            inst.release()

    def make(self):
        inst = SingleInstance(self.key)
        self.instances.append(inst)
        return inst

    def pump(self, ms=300):
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()

    def test_first_acquires_second_is_rejected_and_notifies_first(self):
        first, second = self.make(), self.make()
        received = []
        first.activation_requested.connect(received.append)
        self.assertTrue(first.try_acquire())

        # A real second launch is a separate process, so the first process's
        # Qt event loop continues running while the second connects and writes.
        # Run the client attempt on a worker thread to model that concurrency;
        # calling try_acquire() inline would block this test's event loop.
        outcome = {}
        finished = threading.Event()

        def attempt_second_launch():
            try:
                outcome["acquired"] = second.try_acquire()
            except BaseException as exc:
                outcome["error"] = exc
            finally:
                finished.set()

        worker = threading.Thread(target=attempt_second_launch, daemon=True)
        worker.start()

        loop = QEventLoop()
        poll = QTimer()
        poll.setInterval(10)
        poll.timeout.connect(lambda: loop.quit() if finished.is_set() else None)
        poll.start()
        QTimer.singleShot(2000, loop.quit)
        loop.exec()
        poll.stop()
        worker.join(timeout=1)

        self.assertTrue(finished.is_set(), "second-launch attempt timed out")
        if "error" in outcome:
            raise outcome["error"]
        self.assertFalse(outcome["acquired"], "second launch should be rejected")
        self.pump()
        self.assertEqual(received, ["show"])

    def test_release_allows_a_later_launch(self):
        first = self.make()
        self.assertTrue(first.try_acquire())
        first.release()
        self.assertTrue(self.make().try_acquire())


if __name__ == "__main__":
    unittest.main()
