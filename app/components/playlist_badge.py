#components/playlist_badge.py
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt5.QtWidgets import QWidget


class PlaylistBadge(QWidget):
    """
    Visual playlist badge (similar to cover art).
    A solid-colored square with rounded corners, featuring initials.

    Examples:
        'Evening Chill' -> 'EC'
        'Work Mix'      -> 'WM'
        'Focus'         -> 'F'
        'My Super Long' -> 'MSL'
    """

    def __init__(self, initials: str = "", color: str = "#1DB954", size: int = 40, parent=None):
        super().__init__(parent)
        self._initials = initials
        self._color = QColor(color)
        self._size = size
        self.setFixedSize(size, size)

    # Public methods

    def set_initials(self, initials: str) -> None:
        self._initials = initials[:4].upper()
        self.update()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def set_size(self, size: int) -> None:
        self._size = size
        self.setFixedSize(size, size)
        self.update()

    # Paint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # rounded rectangle (6px)
        rect = QRectF(0, 0, self._size, self._size)
        radius = 6.0
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # background fill
        painter.fillPath(path, self._color)

        # initials text
        font_size = max(10, self._size // 3)
        font = QFont("Segoe UI", font_size, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(rect, Qt.AlignCenter, self._initials)

        painter.end()