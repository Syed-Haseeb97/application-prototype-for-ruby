"""Application lifecycle: tray, orb visibility, settings, second launch, quit.

``RubyApp`` knows nothing about Gemini or voice. It drives an "orb" object
(``FloatingButton`` in production) through a small interface:
``open_chat()``, ``trigger()``, ``is_orb_visible()``, ``set_orb_visible(bool)``
and ``shutdown()``.
"""
from __future__ import annotations

import logging

from PyQt6.QtCore import QObject

from core import paths
from core.startup import StartupError

log = logging.getLogger("ruby.app")


class RubyApp(QObject):
    def __init__(self, qapp, orb, settings, tray, startup, single_instance=None,
                 services=(), dialog_factory=None):
        super().__init__()
        self.qapp, self.orb, self.settings = qapp, orb, settings
        self.tray, self.startup, self.single = tray, startup, single_instance
        self.services = list(services)
        self._dialog_factory = dialog_factory
        self._dialog = None
        self._shut_down = False

        tray.open_requested.connect(self.open_chat)
        tray.type_requested.connect(self.open_chat)
        tray.toggle_orb_requested.connect(self.toggle_orb)
        tray.voice_requested.connect(self.ask_by_voice)
        tray.settings_requested.connect(self.open_settings)
        tray.start_with_windows_toggled.connect(self.set_start_with_windows)
        tray.quit_requested.connect(self.quit)
        if single_instance is not None:
            single_instance.activation_requested.connect(self.on_second_launch)
        chat = getattr(orb, "response_popup", None)
        if chat is not None and hasattr(chat, "settings_requested"):
            chat.settings_requested.connect(self.open_settings)
        qapp.aboutToQuit.connect(self.shutdown)

    # ---- startup -------------------------------------------------------
    def start(self) -> None:
        tray_ok = self.tray.show()
        if self.startup.supported:
            enabled = self.startup.is_enabled()  # the registry is the source of truth
            self.settings.set("start_with_windows", enabled)
            self.tray.set_start_with_windows(enabled)
        # Without a tray the orb is the only way to reach Ruby: never hide it.
        visible = self.settings.orb_visible or not tray_ok
        self.orb.set_orb_visible(visible)
        self.tray.set_orb_visible(visible)
        if not self.settings.get("first_run_done", False):
            self.settings.set("first_run_done", True)
            self.tray.notify("Ruby is running", "Use the orb, or right-click the tray icon for options.")
            if not paths.has_api_key():
                self.open_settings()

    # ---- actions -------------------------------------------------------
    def open_chat(self) -> None:
        self.orb.open_chat()

    def ask_by_voice(self) -> None:
        self.orb.trigger()

    def toggle_orb(self) -> None:
        self.set_orb_visible(not self.orb.is_orb_visible())

    def set_orb_visible(self, visible: bool) -> None:
        if not visible and not self.tray.available:
            log.warning("Refusing to hide the orb: no system tray to restore it from")
            visible = True
        self.orb.set_orb_visible(visible)
        self.settings.set("orb_visible", visible)
        self.tray.set_orb_visible(visible)
        if self._dialog is not None:
            self._dialog.set_orb_checked(visible)

    def set_start_with_windows(self, enabled: bool) -> None:
        try:
            self.startup.set_enabled(enabled)
        except StartupError as exc:
            log.error("%s", exc)
            actual = self.startup.is_enabled()
            self.tray.set_start_with_windows(actual)
            if self._dialog is not None:
                self._dialog.set_startup_checked(actual)
            self.tray.notify("Ruby", str(exc))
            return
        self.settings.set("start_with_windows", enabled)
        self.tray.set_start_with_windows(enabled)
        if self._dialog is not None:
            self._dialog.set_startup_checked(enabled)

    def open_settings(self) -> None:
        if self._dialog is None:
            if self._dialog_factory is None:
                from ui.settings_dialog import SettingsDialog
                self._dialog_factory = lambda: SettingsDialog(self.settings, self.startup.supported)
            self._dialog = self._dialog_factory()
            self._dialog.orb_visible_changed.connect(self.set_orb_visible)
            self._dialog.start_with_windows_changed.connect(self.set_start_with_windows)
        self._dialog.refresh_key_status()
        self._dialog.show()
        self._dialog.raise_()
        self._dialog.activateWindow()

    def on_second_launch(self, _command: str = "show") -> None:
        """A second launch must reveal this instance, never create another."""
        if not self.orb.is_orb_visible():
            self.set_orb_visible(True)
        self.open_chat()

    # ---- shutdown ------------------------------------------------------
    def quit(self) -> None:
        self.shutdown()
        self.qapp.quit()

    def shutdown(self) -> None:
        if self._shut_down:
            return
        self._shut_down = True
        for service in self.services:
            try:
                service.stop()
            except Exception:
                log.exception("Failed stopping %r", service)
        try:
            self.orb.shutdown()
        except Exception:
            log.exception("Orb shutdown failed")
        if self._dialog is not None:
            self._dialog.close()
        self.tray.hide()
        if self.single is not None:
            self.single.release()
