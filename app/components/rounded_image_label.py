# components/rounded_image_label.py
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPainterPath, QPixmap
from PyQt5.QtWidgets import QLabel

class RoundedImageLabel(QLabel):
    """QLabel, which crop QPixmap to rounded corners."""
    def __init__(self, radius: int = 8, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._pixmap = QPixmap()
        self._radius = radius
        self.setStyleSheet("background: #222222;")

    def setPixmap(self, pixmap):
        """Set pixmap for RoundedImageLabel object and update it."""
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        """Override of base paint event.
        Create path for clipping and add round on the corners.
        """
        if self._pixmap.isNull():
            super().paintEvent(event)
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
        # Centering the image
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        
        # Create path for clipping
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._radius, self._radius)
        
        painter.setClipPath(path)
        painter.drawPixmap(x, y, scaled)
