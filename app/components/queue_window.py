# components/queue_window.py
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ScrollArea

from app.core.app_state import AppState
from app.core.metadata_reader import MetadataReader
from .marquee_label import MarqueeLabel
from .rounded_image_label import RoundedImageLabel
from .queue_list_container import QueueListContainer

class QueueWindow(QWidget):
    """Window for queue.
    Contains current track info and queue list.
    """
    queue_reordered = pyqtSignal(list)
    play_track_requested = pyqtSignal(Path)

    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.setObjectName("QueueWindow")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.setStyleSheet("""
            #QueueWindow {
                background-color: #111111;
                border-radius: 10px;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8,12,8,12)
        self.main_layout.setSpacing(12)
        
        # Current track info
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(0)
        self.info_layout.setContentsMargins(5,0,5,0)
        self.info_layout.setAlignment(Qt.AlignCenter)
        
        self.cover_label = RoundedImageLabel(radius=6)
        self.cover_label.setFixedSize(225, 225)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet("""
            QLabel {
                background: #222222;
                border-radius: 8px;
            }
        """)
        
        self.title_label = MarqueeLabel("No track selected")
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold; background: transparent;")
        self.title_label.setAlignment(Qt.AlignLeft)
        
        self.artist_label = MarqueeLabel("Unknown Artist")
        self.artist_label.setStyleSheet("color: #AAAAAA; font-size: 14px; background: transparent;")
        self.artist_label.setAlignment(Qt.AlignLeft)
        
        self.info_layout.addWidget(self.cover_label, alignment=Qt.AlignCenter)
        self.info_layout.addSpacing(5)
        self.info_layout.addWidget(self.title_label)
        self.info_layout.addSpacing(5)
        self.info_layout.addWidget(self.artist_label)
        
        self.main_layout.addLayout(self.info_layout)
        
        # Queue list
        self.queue_scroll = ScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setStyleSheet("""
            ScrollArea, ScrollArea::viewport, ScrollArea > QWidget > QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.queue_list = QueueListContainer()
        self.queue_list.order_changed.connect(self.__on_order_changed)
        self.queue_list.track_double_clicked.connect(self.__on_track_double_clicked)
        
        self.queue_scroll.setWidget(self.queue_list)
        self.main_layout.addWidget(self.queue_scroll, stretch=1)
        
        # Init date
        self.__update_current_track()
        self._update_queue()


    def __update_current_track(self):
        """Update current track info."""
        current_path = self.app_state.current_track_path
        if current_path and current_path.exists():
            meta = MetadataReader.get_metadata(current_path)
            self.title_label._setText(meta.get('title', current_path.stem))
            self.artist_label._setText(meta.get('artist', 'Unknown Artist'))
            
            if meta.get('cover_data'):
                pixmap = QPixmap()
                if pixmap.loadFromData(meta['cover_data']) and not pixmap.isNull():
                    self.cover_label.setPixmap(pixmap)
                else:
                    self.cover_label.clear()
            else:
                self.cover_label.clear()
        else:
            self.title_label._setText("No track selected")
            self.artist_label._setText("Unknown Artist")
            self.cover_label.clear()

        
    def __on_order_changed(self, new_order: list[Path]):
        """Update AppState playlist after changing queue."""
        self.app_state.playlist_paths = new_order
        self.queue_reordered.emit(new_order)
    

    def __on_track_double_clicked(self, track_path: Path):
        """Handling double click on a track in the queue to play track.
        Emit play_track signal."""
        self.play_track_requested.emit(track_path)


    def _set_no_cover_pixmap(self):
        """Create empty pixmap with text 'No Cover' and set it in label."""
        pixmap = QPixmap(225, 225)
        pixmap.fill(QColor("#222222"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
    
        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        painter.setPen(QColor("#555555")) 
        
        text = "No Cover"
        rect = QRectF(0, 0, 225, 225)
        painter.drawText(rect, Qt.AlignCenter, text)
        
        painter.end()
        
        self.cover_label.setPixmap(pixmap)


    def _update_queue(self):
        """Update queue list."""
        tracks = self.app_state.playlist_paths
        current_track = self.app_state.current_track_path
        self.queue_list._set_tracks(tracks, current_track)
        
        
    def _on_track_changed(self, title: str, artist: str, album: str, cover_data: object):
        """Update queue window data after changing track from player.
        Change info about current track. Get actual data from app_state.
        """
        self.title_label._setText(title)
        self.artist_label._setText(artist)
        
        if cover_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(cover_data) and not pixmap.isNull():
                self.cover_label.setPixmap(pixmap)
            else:
                self._set_no_cover_pixmap()
        else:
            self._set_no_cover_pixmap()
        
        self.queue_list._update_current_highlight(self.app_state.current_track_path)
        self._update_queue()
    