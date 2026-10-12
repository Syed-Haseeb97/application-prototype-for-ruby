"""Ruby's application/tray icon (bundled file with a painted fallback)."""
from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QRadialGradient

from core import paths


def _painted_icon(size: int = 64) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QRadialGradient(QPointF(size * 0.38, size * 0.34), size * 0.62)
    grad.setColorAt(0.0, QColor("#c4b5fd"))
    grad.setColorAt(1.0, QColor("#5b21b6"))
    p.setBrush(grad)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(int(size * 0.08), int(size * 0.08), int(size * 0.84), int(size * 0.84))
    p.end()
    return QIcon(pix)


def build_app_icon() -> QIcon:
    for name in ("ruby.ico", "ruby.png"):
        path = paths.resource_path("assets", name)
        if path.is_file():
            icon = QIcon(str(path))
            if not icon.isNull():
                return icon
    return _painted_icon()
