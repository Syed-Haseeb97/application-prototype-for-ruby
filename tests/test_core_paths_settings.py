"""Pure-Python tests (no Qt): path resolution and settings persistence."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import paths
from core.settings import Settings


class PathTests(unittest.TestCase):
    def test_user_data_dir_override_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "ruby"
            with mock.patch.dict(os.environ, {"RUBY_DATA_DIR": str(target)}):
                self.assertEqual(paths.user_data_dir(), target)
                self.assertTrue(target.is_dir())
                self.assertEqual(paths.preferences_file(), target / "preferences.json")
                self.assertEqual(paths.log_file().parent, target / "logs")

    def test_source_checkout_resources_resolve_from_repo_root(self):
        self.assertTrue(paths.resource_path("main.py").is_file())

    def test_frozen_resources_use_meipass(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(sys, "_MEIPASS", tmp, create=True):
            self.assertEqual(paths.resource_dir(), Path(tmp))
            self.assertEqual(paths.resource_path("assets", "ruby.ico"), Path(tmp) / "assets" / "ruby.ico")

    def test_env_loading_never_overrides_real_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text("GEMINI_API_KEY=from_file\nRUBY_TEST_ONLY=1\n")
            with mock.patch.dict(os.environ, {"RUBY_DATA_DIR": tmp, "GEMINI_API_KEY": "real"}):
                os.environ.pop("RUBY_TEST_ONLY", None)
                self.assertEqual(paths.load_environment(), Path(tmp) / ".env")
                self.assertEqual(os.environ["GEMINI_API_KEY"], "real")
                self.assertEqual(os.environ["RUBY_TEST_ONLY"], "1")
                os.environ.pop("RUBY_TEST_ONLY", None)

    def test_placeholder_key_is_not_a_key(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "your_gemini_api_key_here"}):
            self.assertFalse(paths.has_api_key())
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "abc"}):
            self.assertTrue(paths.has_api_key())

    def test_media_dirs_are_not_hardcoded_to_a_drive(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RUBY_SCREENSHOTS_DIR", None)
            self.assertNotIn("D:", str(paths.media_dir("screenshots")))


class SettingsTests(unittest.TestCase):
    def test_defaults_then_persistence_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "preferences.json"
            s = Settings(file)
            self.assertTrue(s.orb_visible)
            self.assertFalse(s.start_with_windows)
            s.set("orb_visible", False)
            self.assertFalse(Settings(file).orb_visible)

    def test_unknown_keys_written_by_other_modules_survive(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "preferences.json"
            file.write_text(json.dumps({"voice": "en-US-AriaNeural", "personality": "concise"}))
            s = Settings(file)
            s.set("orb_visible", False)
            data = json.loads(file.read_text())
            self.assertEqual(data["voice"], "en-US-AriaNeural")
            self.assertEqual(data["personality"], "concise")

    def test_set_merges_keys_written_after_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "preferences.json"
            s = Settings(file)
            file.write_text(json.dumps({"voice": "x"}))  # another module writes
            s.set("orb_visible", False)
            self.assertEqual(json.loads(file.read_text())["voice"], "x")

    def test_corrupt_file_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "preferences.json"
            file.write_text("{not json")
            s = Settings(file)
            self.assertTrue(s.orb_visible)
            s.set("orb_visible", False)  # recovers by rewriting a valid file
            self.assertFalse(json.loads(file.read_text())["orb_visible"])


if __name__ == "__main__":
    unittest.main()
