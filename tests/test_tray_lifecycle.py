"""Tray menu + application lifecycle, using a fake orb (offscreen Qt)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from core.settings import Settings
from core.startup import StartupManager
from ruby_app import RubyApp
from ui.app_icon import build_app_icon
from ui.tray import TrayController


class FakeRegistry:
    def __init__(self):
        self.values, self.fail = {}, False

    def get(self, name):
        return self.values.get(name)

    def set(self, name, value):
        if self.fail:
            raise PermissionError("denied")
        self.values[name] = value

    def delete(self, name):
        if self.fail:
            raise PermissionError("denied")
        self.values.pop(name, None)


class FakeOrb:
    def __init__(self):
        self.visible = True
        self.calls = []

    def is_orb_visible(self):
        return self.visible

    def set_orb_visible(self, v):
        self.visible = v
        self.calls.append(("visible", v))

    def open_chat(self):
        self.calls.append("chat")

    def trigger(self):
        self.calls.append("voice")

    def shutdown(self):
        self.calls.append("shutdown")


class FakeSingle(QObject):
    activation_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.released = False

    def release(self):
        self.released = True


class FakeService:
    stopped = False

    def stop(self):
        self.stopped = True


class FakeDialog(QObject):
    orb_visible_changed = pyqtSignal(bool)
    start_with_windows_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.shown = 0
        self.closed = False

    def refresh_key_status(self): pass
    def show(self): self.shown += 1
    def raise_(self): pass
    def activateWindow(self): pass
    def close(self): self.closed = True
    def set_orb_checked(self, v): pass
    def set_startup_checked(self, v): pass


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(Path(self.tmp.name) / "preferences.json")
        self.settings.set("first_run_done", True)
        self.registry = FakeRegistry()
        self.startup = StartupManager(self.registry, command="ruby.exe")
        self.orb, self.single, self.service = FakeOrb(), FakeSingle(), FakeService()
        self.dialog = FakeDialog()
        self.tray = TrayController(build_app_icon(), True, False, True)
        self.tray.available = True  # offscreen has no real tray; behave as if it does
        self.qapp = mock.MagicMock()
        self.ruby = RubyApp(self.qapp, self.orb, self.settings, self.tray, self.startup,
                            self.single, [self.service], dialog_factory=lambda: self.dialog)

    def tearDown(self):
        self.tray.tray.hide()
        self.tmp.cleanup()

    def test_menu_has_every_required_item_and_no_dead_ones(self):
        labels = [a.text() for a in self.tray.menu.actions() if not a.isSeparator()]
        self.assertEqual(labels, ["Open Ruby", "Hide Orb", "Ask by Voice / Interrupt",
                                  "Type a Question", "Settings…", "Start with Windows", "Quit Ruby"])

    def test_open_and_type_actions_open_chat_without_quitting(self):
        self.tray.open_action.trigger()
        self.tray.type_action.trigger()
        self.assertEqual(self.orb.calls, ["chat", "chat"])
        self.qapp.quit.assert_not_called()

    def test_voice_action_triggers_existing_voice_path(self):
        self.tray.voice_action.trigger()
        self.assertEqual(self.orb.calls, ["voice"])

    def test_hide_then_show_orb_keeps_app_alive_and_persists(self):
        self.tray.toggle_orb_action.trigger()
        self.assertFalse(self.orb.visible)
        self.assertEqual(self.tray.toggle_orb_action.text(), "Show Orb")
        self.assertFalse(self.settings.orb_visible)
        self.qapp.quit.assert_not_called()
        self.tray.toggle_orb_action.trigger()
        self.assertTrue(self.orb.visible)
        self.assertEqual(self.tray.toggle_orb_action.text(), "Hide Orb")

    def test_orb_cannot_be_hidden_without_a_tray(self):
        self.tray.available = False
        self.ruby.set_orb_visible(False)
        self.assertTrue(self.orb.visible)

    def test_start_with_windows_toggle_writes_and_clears_registry(self):
        self.tray.startup_action.setChecked(True)
        self.assertEqual(self.registry.values.get("RubyAI"), "ruby.exe")
        self.assertTrue(self.settings.start_with_windows)
        self.tray.startup_action.setChecked(False)
        self.assertEqual(self.registry.values, {})
        self.assertFalse(self.settings.start_with_windows)

    def test_failed_startup_change_reverts_the_checkmark(self):
        self.registry.fail = True
        self.tray.startup_action.setChecked(True)
        self.assertFalse(self.tray.startup_action.isChecked())
        self.assertFalse(self.settings.start_with_windows)

    def test_settings_action_opens_one_reusable_dialog(self):
        self.tray.settings_action.trigger()
        self.tray.settings_action.trigger()
        self.assertEqual(self.dialog.shown, 2)

    def test_second_launch_reveals_hidden_orb_and_opens_chat(self):
        self.ruby.set_orb_visible(False)
        self.single.activation_requested.emit("show")
        self.assertTrue(self.orb.visible)
        self.assertEqual(self.orb.calls[-1], "chat")

    def test_quit_cleans_up_once_and_quits_the_event_loop(self):
        self.tray.quit_action.trigger()
        self.ruby.shutdown()  # aboutToQuit calling it again must be harmless
        self.assertTrue(self.service.stopped)
        self.assertEqual(self.orb.calls.count("shutdown"), 1)
        self.assertTrue(self.single.released)
        self.qapp.quit.assert_called_once()

    def test_start_syncs_checkmark_from_registry(self):
        self.registry.values["RubyAI"] = "ruby.exe"
        self.ruby.start()
        self.assertTrue(self.tray.startup_action.isChecked())

    def test_app_icon_is_never_null(self):
        self.assertFalse(build_app_icon().isNull())


if __name__ == "__main__":
    unittest.main()
