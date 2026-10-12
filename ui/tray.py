"""System-tray controller: the always-available way to drive Ruby."""
from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

log = logging.getLogger("ruby.tray")


class TrayController(QObject):
    open_requested = pyqtSignal()
    toggle_orb_requested = pyqtSignal()
    voice_requested = pyqtSignal()
    type_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    start_with_windows_toggled = pyqtSignal(bool)
    quit_requested = pyqtSignal()

    def __init__(self, icon: QIcon, orb_visible: bool = True, start_with_windows: bool = False,
                 startup_supported: bool = True, parent=None):
        super().__init__(parent)
        self.available = QSystemTrayIcon.isSystemTrayAvailable()
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("Ruby")
        self.menu = QMenu()

        self.open_action = self.menu.addAction("Open Ruby")
        font = self.open_action.font()
        font.setBold(True)
        self.open_action.setFont(font)
        self.toggle_orb_action = self.menu.addAction("Hide Orb")
        self.menu.addSeparator()
        self.voice_action = self.menu.addAction("Ask by Voice / Interrupt")
        self.type_action = self.menu.addAction("Type a Question")
        self.menu.addSeparator()
        self.settings_action = self.menu.addAction("Settings…")
        self.startup_action: QAction = self.menu.addAction("Start with Windows")
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(start_with_windows)
        self.startup_action.setEnabled(startup_supported)
        self.menu.addSeparator()
        self.quit_action = self.menu.addAction("Quit Ruby")

        self.open_action.triggered.connect(self.open_requested)
        self.toggle_orb_action.triggered.connect(self.toggle_orb_requested)
        self.voice_action.triggered.connect(self.voice_requested)
        self.type_action.triggered.connect(self.type_requested)
        self.settings_action.triggered.connect(self.settings_requested)
        self.startup_action.toggled.connect(self.start_with_windows_toggled)
        self.quit_action.triggered.connect(self.quit_requested)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)
        self.set_orb_visible(orb_visible)

    def show(self) -> bool:
        if not self.available:
            log.warning("No system tray available; tray controls disabled")
            return False
        self.tray.show()
        return True

    def hide(self) -> None:
        self.tray.hide()  # removes the icon so no ghost is left behind

    def set_orb_visible(self, visible: bool) -> None:
        self.toggle_orb_action.setText("Hide Orb" if visible else "Show Orb")

    def set_start_with_windows(self, enabled: bool) -> None:
        """Update the check mark without re-emitting the toggled signal."""
        blocked = self.startup_action.blockSignals(True)
        self.startup_action.setChecked(enabled)
        self.startup_action.blockSignals(blocked)

    def notify(self, title: str, message: str) -> None:
        if self.available:
            self.tray.showMessage(title, message, self.tray.icon(), 4000)

    def _on_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self.open_requested.emit()
