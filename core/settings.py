"""Small JSON settings store shared with Ruby's existing preferences.json.

The file also holds keys owned by other modules (``voice``, ``personality``,
``wake_word_enabled``); unknown keys are always preserved.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from core import paths

log = logging.getLogger("ruby.settings")

DEFAULTS: dict[str, Any] = {
    "orb_visible": True,
    "start_with_windows": False,
    "wake_word_enabled": False,
    "first_run_done": False,
}


class Settings:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else paths.preferences_file()
        self._lock = threading.RLock()
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        with self._lock:
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self._data = raw if isinstance(raw, dict) else {}
            except FileNotFoundError:
                self._data = {}
            except (OSError, ValueError) as exc:
                log.warning("Ignoring unreadable settings file %s: %s", self.path, exc)
                self._data = {}

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key in self._data:
                return self._data[key]
        return DEFAULTS.get(key, default) if default is None else default

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self.load()  # merge keys other modules wrote meanwhile
            self._data[key] = value
            self._write()

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".prefs-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    @property
    def orb_visible(self) -> bool:
        return bool(self.get("orb_visible"))

    @property
    def start_with_windows(self) -> bool:
        return bool(self.get("start_with_windows"))
