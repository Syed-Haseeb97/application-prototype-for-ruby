"""Location helpers that work from source checkouts and PyInstaller builds.

* ``resource_path`` – read-only files shipped with Ruby (icons, .env.example).
* ``user_data_dir`` – writable per-user data (preferences, memory, logs, .env).
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

APP_NAME = "Ruby"
_SOURCE_ROOT = Path(__file__).resolve().parent.parent


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """Directory containing the executable (frozen) or the repository root."""
    return Path(sys.executable).resolve().parent if is_frozen() else _SOURCE_ROOT


def resource_dir() -> Path:
    """Root of bundled read-only resources."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", app_dir()))
    return _SOURCE_ROOT


def resource_path(*parts: str) -> Path:
    return resource_dir().joinpath(*parts)


def user_data_dir(create: bool = True) -> Path:
    """Writable per-user directory. ``RUBY_DATA_DIR`` overrides (used by tests)."""
    override = os.environ.get("RUBY_DATA_DIR", "").strip()
    if override:
        path = Path(override)
    elif sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        path = Path(base) / APP_NAME
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        path = Path(base) / APP_NAME
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def preferences_file() -> Path:
    return user_data_dir() / "preferences.json"


def memory_file() -> Path:
    return user_data_dir() / "memory.json"


def env_file() -> Path:
    return user_data_dir() / ".env"


def log_file() -> Path:
    logs = user_data_dir() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs / "ruby.log"


def media_dir(kind: str) -> Path:
    """Default folder for screenshots/recordings (``RUBY_<KIND>_DIR`` overrides)."""
    override = os.environ.get(f"RUBY_{kind.upper()}_DIR", "").strip()
    if override:
        return Path(override)
    pictures = Path.home() / ("Videos" if kind.lower() == "recordings" else "Pictures")
    return pictures / "Ruby" / kind.capitalize()


def migrate_legacy_files() -> list[str]:
    """Copy preferences/memory from an old source checkout (never overwrites)."""
    moved: list[str] = []
    for name in ("preferences.json", "memory.json"):
        old, new = _SOURCE_ROOT / name, user_data_dir() / name
        if not is_frozen() and old.is_file() and not new.exists():
            try:
                shutil.copy2(old, new)
                moved.append(name)
            except OSError:
                pass
    return moved


def env_candidates() -> list[Path]:
    """.env search order: user data dir, next to the exe/repo, current directory."""
    return [env_file(), app_dir() / ".env", Path.cwd() / ".env"]


def load_environment() -> Path | None:
    """Load the first existing .env without overriding real environment variables."""
    from dotenv import load_dotenv

    for candidate in env_candidates():
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            return candidate
    return None


def has_api_key() -> bool:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    return bool(key) and key != "your_gemini_api_key_here"
