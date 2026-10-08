#components/playlist_badge.py
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt5.QtWidgets import QWidget


def draw_badge(painter: QPainter, rect: QRectF, color: QColor, initials: str,
               radius: float = 6.0) -> None:
    """Draw the badge (rounded square + initials) using an existing painter.
    Shared by PlaylistBadge widget and PlaylistNavItem."""
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    painter.fillPath(path, color)

    # Adaptive font size by character count
    num_chars = len(initials)
    base = rect.height()
    if num_chars <= 1:
        font_size = base / 2
    elif num_chars <= 3:
        font_size = base / 3
    else:
        font_size = base / 4
    font = QFont("Segoe UI", max(7, int(font_size)), QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#FFFFFF"))
    painter.drawText(rect, Qt.AlignCenter, initials)


class PlaylistBadge(QWidget):
    """
    Visual playlist badge (similar to cover art).
    A solid-colored square with rounded corners, featuring initials.
    Examples:
        'Evening Chill' -> 'EC'
        'Work Mix'      -> 'WM'
        'Focus'         -> 'F'
        'My Super Long' -> 'MSLP'
    """

    def __init__(self, initials: str = "", color: str = "#1DB954", size: int = 40, parent=None):
        super().__init__(parent)
        self._initials = initials
        self._color = QColor(color)
        self._size = size
        self.setFixedSize(size, size)

    # ==================== Public methods ====================
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

    # ==================== Paint ====================
    def paintEvent(self, event):
        painter = QPainter(self)
        draw_badge(
            painter,
            QRectF(0, 0, self._size, self._size),
            self._color,
            self._initials,
        )
        painter.end()