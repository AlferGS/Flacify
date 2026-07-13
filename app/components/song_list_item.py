# app/components/song_list_item.py
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QBrush, QPixmap
from qfluentwidgets import BodyLabel, CardWidget, Theme, FluentIcon as FIF

from app.utils import sanitize_metadata_text


class SongListItem(CardWidget):
    itemClicked = pyqtSignal(str)

    def __init__(self, file_name:str, song_name: str, artist: str = "Unknown Artist", 
                 song_dur: str = "00:00", cover_data: bytes = None, parent=None):
        super().__init__(parent)
        self.file_name = file_name
        self.song_name = song_name
        self.artist = artist
        self.song_dur = song_dur
        self.cover_data = cover_data
        sanitized_song_name = sanitize_metadata_text(song_name)
        self.display_name = sanitized_song_name if sanitized_song_name else file_name
        
        sanitized_artist = sanitize_metadata_text(artist)
        self.display_artist = sanitized_artist if sanitized_artist else "Unknown Artist"
        
        self.setFixedHeight(56)
        self.setMinimumWidth(100)
        self.setObjectName("SongListItem")

        # Main layout
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setSpacing(12)
        self.h_layout.setContentsMargins(10, 8, 10, 8)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(40, 40)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet("""
            QLabel {
                background: #222222;
                border-radius: 4px;
            }
        """)

        # Upload a cover or default icon
        self._original_pixmap = self.__load_cover_pixmap()
        self.cover_label.setPixmap(self._original_pixmap)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.title_label = BodyLabel(self.display_name)
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.title_label.setStyleSheet("color: #FFFFFF; font-weight: bold; background: transparent;")
        
        self.artist_label = BodyLabel(self.display_artist)
        self.artist_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.artist_label.setStyleSheet("color: #AAAAAA; font-size: 12px; background: transparent;")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)

        self.dur_label = BodyLabel(self.song_dur)
        self.dur_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.dur_label.setStyleSheet("color: #AAAAAA; background: transparent;")

        self.h_layout.addWidget(self.cover_label)
        self.h_layout.addLayout(text_layout)
        self.h_layout.addStretch(1)
        self.h_layout.addWidget(self.dur_label)

        self.clicked.connect(self.__on_clicked)


    def __load_cover_pixmap(self) -> QPixmap:
        """
        Returns a QPixmap containing either the album cover or the default note icon.
        """
        if self.cover_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(self.cover_data) and not pixmap.isNull():
                return pixmap.scaled(
                    40, 40,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
        
        return FIF.MUSIC.icon(Theme.DARK).pixmap(24, 24)


    def __on_clicked(self):
        """On item click event. Emit itemClicked."""
        self.itemClicked.emit(self.file_name)


    def enterEvent(self, event):
        """Enter on item event."""
        super().enterEvent(event)
        play_pixmap = FIF.PLAY.icon(Theme.DARK).pixmap(24, 24)
        self.cover_label.setPixmap(play_pixmap)


    def leaveEvent(self, event):
        """Leave the item event."""
        super().leaveEvent(event)
        self.cover_label.setPixmap(self._original_pixmap)


    def paintEvent(self, event):
        """Override paint event."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        
        if self.isHover or self.isPressed:
            bg_color = QColor("#1F1F1F")
        else:
            bg_color = QColor("#111111")
            
        painter.fillPath(path, QBrush(bg_color))