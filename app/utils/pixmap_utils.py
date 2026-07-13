# utils/pixmap_utils.py
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect


def blur_pixmap(pixmap: QPixmap, radius: int = 12) -> QPixmap:
    """Create and return blured copy QPixmap."""
    if pixmap.isNull():
        return pixmap
    scene = QGraphicsScene()
    item = QGraphicsPixmapItem(pixmap)
    blur = QGraphicsBlurEffect()
    blur.setBlurRadius(radius)
    item.setGraphicsEffect(blur)
    scene.addItem(item)
    
    blurred = QPixmap(pixmap.size())
    blurred.fill(Qt.transparent)
    painter = QPainter(blurred)
    scene.render(painter)
    painter.end()
    return blurred