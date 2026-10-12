"""Reversible 'Start with Windows' using the per-user Run registry key.

Uses HKEY_CURRENT_USER, so no administrator rights are needed. Disabling just
deletes Ruby's own value.
"""
from __future__ import annotations

import sys
from pathlib import Path

from core import paths

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "RubyAI"  # same value name the voice command already used


class StartupError(RuntimeError):
    pass


class WinregBackend:
    """Thin wrapper over winreg so tests can substitute a fake."""

    def __init__(self):
        import winreg  # raises ImportError off Windows

        self._w = winreg

    def get(self, name: str) -> str | None:
        try:
            with self._w.OpenKey(self._w.HKEY_CURRENT_USER, RUN_KEY, 0, self._w.KEY_READ) as key:
                return str(self._w.QueryValueEx(key, name)[0])
        except FileNotFoundError:
            return None

    def set(self, name: str, value: str) -> None:
        with self._w.CreateKeyEx(self._w.HKEY_CURRENT_USER, RUN_KEY, 0, self._w.KEY_SET_VALUE) as key:
            self._w.SetValueEx(key, name, 0, self._w.REG_SZ, value)

    def delete(self, name: str) -> None:
        try:
            with self._w.OpenKey(self._w.HKEY_CURRENT_USER, RUN_KEY, 0, self._w.KEY_SET_VALUE) as key:
                self._w.DeleteValue(key, name)
        except FileNotFoundError:
            pass


def launch_command() -> str:
    """Command line Windows should run at login (never opens a console)."""
    if paths.is_frozen():
        return f'"{Path(sys.executable).resolve()}"'
    exe = Path(sys.executable)
    pythonw = exe.with_name("pythonw.exe")
    target = pythonw if pythonw.exists() else exe
    return f'"{target}" "{paths.app_dir() / "main.py"}"'


class StartupManager:
    def __init__(self, backend=None, command: str | None = None):
        self._backend = backend
        self._command = command

    def _backend_or_none(self):
        if self._backend is None and sys.platform == "win32":
            self._backend = WinregBackend()
        return self._backend

    @property
    def supported(self) -> bool:
        return self._backend_or_none() is not None

    def is_enabled(self) -> bool:
        backend = self._backend_or_none()
        return bool(backend and backend.get(VALUE_NAME))

    def set_enabled(self, enabled: bool) -> None:
        backend = self._backend_or_none()
        if backend is None:
            raise StartupError("Start with Windows is only available on Windows.")
        try:
            if enabled:
                backend.set(VALUE_NAME, self._command or launch_command())
            else:
                backend.delete(VALUE_NAME)
        except OSError as exc:
            raise StartupError(f"Could not update Windows startup: {exc}") from exc
