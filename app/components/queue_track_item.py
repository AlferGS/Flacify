# components/queue_track_item.py
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPoint
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QBrush, QPixmap, QPen
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication
from qfluentwidgets import BodyLabel, FluentIcon as FIF, Theme

from app.core.metadata_reader import MetadataReader
from app.utils.pixmap_utils import blur_pixmap
from .rounded_image_label import RoundedImageLabel

class QueueTrackItem(QWidget):
    """Widget for one track in queue. Support Drag&Drop."""
    drag_started = pyqtSignal(object)
    drag_moved = pyqtSignal(object, QPoint)
    drag_finished = pyqtSignal(object)
    track_double_clicked = pyqtSignal(Path)

    def __init__(self, track_path: Path, is_current: bool, parent=None):
        super().__init__(parent)
        self.track_path = track_path
        self.is_current = is_current
        self.is_dragging = False
        
        self.setFixedHeight(56)
        self.setObjectName("QueueTrackItem")
        
        # Main horizontal layout
        h_layout = QHBoxLayout(self)
        h_layout.setSpacing(10)
        h_layout.setContentsMargins(8, 8, 8, 8)
        
        # Album cover
        self.cover_label = RoundedImageLabel(radius=4) 
        self.cover_label.setFixedSize(40, 40)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet("""
            QLabel {
                background: #222222;
                border-radius: 4px;
            }
        """)
        # PLAY icon on top of the cover
        self.play_icon_label = QLabel(self.cover_label)
        self.play_icon_label.setFixedSize(40, 40)
        self.play_icon_label.setAlignment(Qt.AlignCenter)
        self.play_icon_label.setStyleSheet("background: transparent;")
        self.play_icon_label.move(0, 0)
        self.play_icon_label.hide()

        # Cache for blured pixmap
        self._blurred_pixmap = None
        
        meta = MetadataReader.get_metadata(track_path)
        cover_pixmap = self._load_cover_pixmap(meta, track_path)
        self.cover_label.setPixmap(cover_pixmap)
        self._original_pixmap = cover_pixmap
                
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        # Colors for text depends on the state
        title_color = "#1DB954" if self.is_current else "#FFFFFF"
        artist_color = "#1DB954" if self.is_current else "#AAAAAA"
        
        self.title_label = BodyLabel(meta.get('title', track_path.stem))
        self.title_label.setStyleSheet(f"color: {title_color}; font-weight: bold; background: transparent;")

        self.artist_label = BodyLabel(meta.get('artist', 'Unknown Artist'))
        self.artist_label.setStyleSheet(f"color: {artist_color}; font-size: 12px; background: transparent;")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)
        text_layout.addStretch() 
        
        h_layout.addWidget(self.cover_label)
        h_layout.addLayout(text_layout, stretch=1) 
        
    def paintEvent(self, event):
        """Custom background and frame rendering for the current track."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        
        if self.is_current:
            bg_color = QColor("#1A3A2A") 
            border_color = QColor("#1DB954")
        else:
            bg_color = QColor("#111111")
            border_color = QColor("transparent")
            
        painter.fillPath(path, QBrush(bg_color))
        if self.is_current:
            pen = QPen(border_color, 1.5)
            painter.setPen(pen)
            painter.drawPath(path)

    def mousePressEvent(self, event):
        """Mouse press on element event. 
        Change state is_dragging to False
        """
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.is_dragging = False
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """Move element event. 
        Change state is_dragging to True and emit drag_started
        """
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self.is_dragging:
            if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
                return
            self.is_dragging = True
            self.drag_started.emit(self)
        
        self.drag_moved.emit(self, event.globalPos())

    def mouseReleaseEvent(self, event):
        """Drop element event. 
        Change state is_dragging to False and emit drag_finished
        """
        if self.is_dragging:
            self.drag_finished.emit(self)
        self.is_dragging = False
        self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        """Catch Double Click event for emit play_song."""
        if event.button() == Qt.LeftButton:
            self.track_double_clicked.emit(self.track_path)
        super().mouseDoubleClickEvent(event)

    def enterEvent(self, event):
        """Set blur on cover and enable PLAY icon"""
        super().enterEvent(event)
        play_pixmap = FIF.PLAY.icon(Theme.DARK).pixmap(20, 20) 
        self.play_icon_label.setPixmap(play_pixmap)
        self.play_icon_label.show()
        
        blurred = self._get_blurred_pixmap()
        if blurred and not blurred.isNull():
            self.cover_label.setPixmap(blurred)

    def leaveEvent(self, event):
        """ Return orig album label/icon or FIF.MUSIC"""
        super().leaveEvent(event)
        self.play_icon_label.hide()
        
        if self._original_pixmap and not self._original_pixmap.isNull():
            self.cover_label.setPixmap(self._original_pixmap)

    def _get_blurred_pixmap(self) -> QPixmap:
        """Return blured version of album cover (with cache)."""
        if self._blurred_pixmap is None:
            self._blurred_pixmap = blur_pixmap(self._original_pixmap, radius=6)
        return self._blurred_pixmap

    def _update_text_colors(self):
        """Update text color depends on the state is_current."""
        title_color = "#1DB954" if self.is_current else "#FFFFFF"
        artist_color = "#1DB954" if self.is_current else "#AAAAAA"
        self.title_label.setStyleSheet(f"color: {title_color}; font-weight: bold; background: transparent;")
        self.artist_label.setStyleSheet(f"color: {artist_color}; font-size: 12px; background: transparent;")

    def _load_cover_pixmap(self, meta: dict, track_path: Path) -> QPixmap:
        """Return QPixmap with size 40x40: album cover or FIF.MUSIC."""
        target_pixmap = QPixmap(40, 40)
        target_pixmap.fill(Qt.transparent)

        if meta.get('cover_data'):
            pixmap = QPixmap()
            if pixmap.loadFromData(meta['cover_data']) and not pixmap.isNull():
                scaled_cover = pixmap.scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                painter = QPainter(target_pixmap)
                painter.drawPixmap(0, 0, scaled_cover)
                painter.end()
                return target_pixmap
        
        icon_size = 24
        icon_pixmap = FIF.MUSIC.icon(Theme.DARK).pixmap(icon_size, icon_size)
        
        if not icon_pixmap.isNull():
            painter = QPainter(target_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            x = (40 - icon_size) // 2
            y = (40 - icon_size) // 2
            
            painter.drawPixmap(x, y, icon_pixmap)
            painter.end()
            
        return target_pixmap
