"""Second launches must reach the running instance (offscreen Qt)."""
import os
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
        self.assertFalse(second.try_acquire())
        self.pump()
        self.assertEqual(received, ["show"])

    def test_release_allows_a_later_launch(self):
        first = self.make()
        self.assertTrue(first.try_acquire())
        first.release()
        self.assertTrue(self.make().try_acquire())


if __name__ == "__main__":
    unittest.main()
