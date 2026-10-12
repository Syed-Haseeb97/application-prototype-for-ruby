"""'Start with Windows' logic tested against a fake registry (no Windows needed)."""
import unittest

from core.startup import RUN_KEY, VALUE_NAME, StartupError, StartupManager, launch_command


class FakeRegistry:
    def __init__(self):
        self.values = {}
        self.fail = False

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


class StartupTests(unittest.TestCase):
    def test_enable_then_disable_is_reversible(self):
        reg = FakeRegistry()
        mgr = StartupManager(reg, command='"C:\\Ruby\\Ruby.exe"')
        self.assertFalse(mgr.is_enabled())
        mgr.set_enabled(True)
        self.assertTrue(mgr.is_enabled())
        self.assertEqual(reg.values[VALUE_NAME], '"C:\\Ruby\\Ruby.exe"')
        mgr.set_enabled(False)
        self.assertFalse(mgr.is_enabled())
        self.assertEqual(reg.values, {})

    def test_disable_when_never_enabled_is_harmless(self):
        StartupManager(FakeRegistry()).set_enabled(False)

    def test_registry_failure_becomes_startup_error(self):
        reg = FakeRegistry()
        reg.fail = True
        with self.assertRaises(StartupError):
            StartupManager(reg, command="x").set_enabled(True)

    def test_unsupported_platform_raises_clearly(self):
        mgr = StartupManager()
        mgr._backend_or_none = lambda: None
        self.assertFalse(mgr.supported)
        with self.assertRaises(StartupError):
            mgr.set_enabled(True)

    def test_command_is_quoted_and_points_at_main_when_not_frozen(self):
        cmd = launch_command()
        self.assertTrue(cmd.startswith('"'))
        self.assertIn("main.py", cmd)

    def test_run_key_is_per_user_location(self):
        self.assertIn("CurrentVersion\\Run", RUN_KEY)


if __name__ == "__main__":
    unittest.main()
