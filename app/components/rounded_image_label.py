#components/rounded_image_label.py
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PyQt5.QtWidgets import QLabel


class RoundedImageLabel(QLabel):
    """QLabel, which paints a rounded background and clips QPixmap to rounded corners."""

    def __init__(self, radius: int = 8, background: str = "#222222", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._pixmap = QPixmap()
        self._radius = radius
        self._background = QColor(background)

        # Background is painted in paintEvent, not via QSS.
        self.setStyleSheet("background: transparent; border: none;")

    # ==================== Public ====================
    def setPixmap(self, pixmap: QPixmap) -> None:
        """Set pixmap and update. Kept compatible with QLabel API."""
        self._pixmap = pixmap
        self.update()

    def set_background_color(self, color: str) -> None:
        """Change rounded placeholder background color."""
        self._background = QColor(color)
        self.update()

    # ==================== Paint ====================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )

        path = QPainterPath()
        path.addRoundedRect(
            QRectF(0, 0, self.width(), self.height()),
            self._radius,
            self._radius,
        )

        # Rounded placeholder background.
        painter.fillPath(path, self._background)

        # Cover / icon pixmap, clipped by the same rounded path.
        if not self._pixmap.isNull():
            painter.setClipPath(path)

            scaled = self._pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )

            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2

            painter.drawPixmap(x, y, scaled)

        painter.end()