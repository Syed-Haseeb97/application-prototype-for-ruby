"""Compact settings window. Every control applies immediately and does something real."""
from __future__ import annotations

import os

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from core import paths

_STYLE = """
QDialog { background: #11131d; }
QLabel { color: #eff0fb; background: transparent; }
QLabel#title { font-size: 17px; font-weight: 700; color: #f7f6ff; }
QLabel#hint { color: #999bb3; font-size: 10px; }
QCheckBox { color: #eff0fb; spacing: 10px; font-size: 10pt; padding: 6px 0; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px;
    border: 1px solid #454b69; background: #1a1c2a; }
QCheckBox::indicator:checked { background: #7868ff; border-color: #a78bfa; }
QPushButton { color: #ffffff; background: #25283a; border: 1px solid #454b69;
    border-radius: 10px; padding: 8px 14px; }
QPushButton:hover { background: #30344c; border-color: #8b7cff; }
QPushButton#primary { background: #7868ff; border-color: #a78bfa; }
QPushButton#primary:hover { background: #8b7cff; }
"""


class SettingsDialog(QDialog):
    orb_visible_changed = pyqtSignal(bool)
    start_with_windows_changed = pyqtSignal(bool)
    wake_word_changed = pyqtSignal(bool)

    def __init__(self, settings, startup_supported: bool = True, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Ruby Settings")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setMinimumWidth(420)
        self.setStyleSheet(_STYLE)

        title = QLabel("Ruby settings")
        title.setObjectName("title")

        self.orb_check = QCheckBox("Show the floating orb")
        self.orb_check.setChecked(settings.orb_visible)
        self.startup_check = QCheckBox("Start Ruby with Windows")
        self.startup_check.setChecked(settings.start_with_windows)
        self.startup_check.setEnabled(startup_supported)
        if not startup_supported:
            self.startup_check.setToolTip("Only available on Windows")
        self.wake_check = QCheckBox("Wake word (“Hey Ruby”)")
        self.wake_check.setChecked(bool(settings.get("wake_word_enabled", False)))
        wake_hint = QLabel("Needs the optional openwakeword package and a wake-word model. "
                           "Takes effect the next time Ruby starts.")
        wake_hint.setObjectName("hint")
        wake_hint.setWordWrap(True)

        self.key_label = QLabel()
        self.key_label.setWordWrap(True)
        self.refresh_key_status()
        folder = QPushButton("Open config folder")
        folder.clicked.connect(self.open_config_folder)
        close = QPushButton("Done")
        close.setObjectName("primary")
        close.clicked.connect(self.accept)

        buttons = QHBoxLayout()
        buttons.addWidget(folder)
        buttons.addStretch(1)
        buttons.addWidget(close)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(6)
        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(self.orb_check)
        layout.addWidget(self.startup_check)
        layout.addWidget(self.wake_check)
        layout.addWidget(wake_hint)
        layout.addSpacing(10)
        layout.addWidget(self.key_label)
        layout.addSpacing(10)
        layout.addLayout(buttons)

        self.orb_check.toggled.connect(self.orb_visible_changed)
        self.startup_check.toggled.connect(self.start_with_windows_changed)
        self.wake_check.toggled.connect(self._wake_toggled)

    def _wake_toggled(self, enabled: bool) -> None:
        self.settings.set("wake_word_enabled", enabled)
        self.wake_word_changed.emit(enabled)

    def refresh_key_status(self) -> None:
        if paths.has_api_key():
            self.key_label.setText("✓ Gemini API key found.")
        else:
            self.key_label.setText(
                f"⚠ No Gemini API key yet. Create a file named .env in the config folder with the line "
                f"GEMINI_API_KEY=your_key, then restart Ruby.\n{paths.env_file()}"
            )

    def set_orb_checked(self, visible: bool) -> None:
        blocked = self.orb_check.blockSignals(True)
        self.orb_check.setChecked(visible)
        self.orb_check.blockSignals(blocked)

    def set_startup_checked(self, enabled: bool) -> None:
        blocked = self.startup_check.blockSignals(True)
        self.startup_check.setChecked(enabled)
        self.startup_check.blockSignals(blocked)

    def open_config_folder(self) -> None:
        folder = str(paths.user_data_dir())
        if hasattr(os, "startfile"):
            os.startfile(folder)  # type: ignore[attr-defined]
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
