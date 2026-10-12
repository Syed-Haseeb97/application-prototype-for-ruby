"""Ruby – floating AI desktop assistant for Windows."""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import paths


def _setup_logging() -> None:
    handlers: list[logging.Handler] = []
    try:
        handlers.append(logging.handlers.RotatingFileHandler(
            paths.log_file(), maxBytes=512_000, backupCount=2, encoding="utf-8"))
    except OSError:
        pass
    if sys.stderr is not None:  # None in a windowed (no-console) build
        handlers.append(logging.StreamHandler(sys.stderr))
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    def _hook(exc_type, exc, tb):
        logging.getLogger("ruby").critical("Unhandled exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = _hook


def main() -> int:
    _setup_logging()
    log = logging.getLogger("ruby")
    paths.migrate_legacy_files()
    paths.load_environment()

    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QApplication, QMessageBox

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # closing the chat must never quit Ruby
    app.setApplicationName("Ruby")
    app.setFont(QFont("Segoe UI", 10))

    from core.settings import Settings
    from core.single_instance import SingleInstance
    from core.startup import StartupManager
    from ui.app_icon import build_app_icon

    single = SingleInstance()
    if not single.try_acquire():
        log.info("Ruby is already running; asked it to show itself")
        return 0

    try:
        from hotkey_manager import HotkeyManager
        from ruby_app import RubyApp
        from ui.floating_button import FloatingButton
        from ui.tray import TrayController
        from voice.wake_word import WakeWordService

        icon = build_app_icon()
        app.setWindowIcon(icon)
        settings = Settings()
        startup = StartupManager()
        orb = FloatingButton()
        tray = TrayController(icon, settings.orb_visible, settings.start_with_windows, startup.supported)

        services = []
        hotkey = HotkeyManager(callback=orb.request_trigger)
        try:
            hotkey.start()
            services.append(hotkey)
        except Exception:
            log.exception("Global hotkey unavailable; continuing without it")
        wake_word = WakeWordService(callback=orb.request_trigger)
        wake_word.start()
        services.append(wake_word)

        ruby = RubyApp(app, orb, settings, tray, startup, single, services)
        ruby.start()
    except Exception as exc:
        log.exception("Ruby failed to start")
        single.release()
        QMessageBox.critical(None, "Ruby could not start",
                             f"{exc}\n\nDetails were written to:\n{paths.log_file()}")
        return 1
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
