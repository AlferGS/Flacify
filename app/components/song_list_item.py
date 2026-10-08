#components/song_list_item.py
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QLabel, QVBoxLayout
from qfluentwidgets import BodyLabel, Theme, FluentIcon as FIF
from app.utils import sanitize_metadata_text
from app.utils.pixmap_utils import blur_pixmap
from .rounded_image_label import RoundedImageLabel
from .list_item import ListItemBase


class SongListItem(ListItemBase):
    """Track row: cover + title/artist + duration. Used in browser AND playlists."""
    itemClicked = pyqtSignal(str)

    def __init__(self, file_name: str, song_name: str, artist: str = "Unknown Artist",
                 song_dur: str = "00:00", cover_data: bytes = None,
                 is_current: bool = False, track_path: Path = None,
                 drag_enabled: bool = False, parent=None):
        super().__init__(menu_enabled=True, height=56, drag_enabled=drag_enabled, parent=parent)
        self.file_name = file_name
        self.track_path = track_path
        self.is_current = is_current
        self.song_name = song_name
        self.artist = artist
        self.song_dur = song_dur
        self.cover_data = cover_data

        sanitized_song_name = sanitize_metadata_text(song_name)
        self.display_name = sanitized_song_name if sanitized_song_name else file_name
        sanitized_artist = sanitize_metadata_text(artist)
        self.display_artist = sanitized_artist if sanitized_artist else "Unknown Artist"

        self.setObjectName("SongListItem")
        self.h_layout.setSpacing(12)
        self.h_layout.setContentsMargins(10, 8, 10, 8)

        self.cover_label = RoundedImageLabel(radius=4)
        self.cover_label.setFixedSize(40, 40)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.play_icon_label = QLabel(self.cover_label)
        self.play_icon_label.setFixedSize(40, 40)
        self.play_icon_label.setAlignment(Qt.AlignCenter)
        self.play_icon_label.setStyleSheet("background: transparent;")
        self.play_icon_label.move(0, 0)
        self.play_icon_label.hide()

        self._original_pixmap = self.__load_cover_pixmap()
        self._blurred_pixmap = None
        self.cover_label.setPixmap(self._original_pixmap)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_color = "#1DB954" if self.is_current else "#FFFFFF"
        self.title_label = BodyLabel(self.display_name)
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.title_label.setStyleSheet(f"color: {title_color}; font-weight: bold; background: transparent;")
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
        self.h_layout.addWidget(self.menu_button)

        self.clicked.connect(self.__on_clicked)

    # ==================== Public ====================
    def _set_current(self, flag: bool) -> None:
        """Toggle current-track highlight (green title)."""
        if self.is_current == flag:
            return
        self.is_current = flag
        color = "#1DB954" if flag else "#FFFFFF"
        self.title_label.setStyleSheet(f"color: {color}; font-weight: bold; background: transparent;")

    # ==================== Protected ====================
    def __load_cover_pixmap(self) -> QPixmap:
        """
        Return 40x40 pixmap.

        - If cover exists: scaled cover filling 40x40.
        - If no cover: transparent 40x40 canvas with 24x24 music icon centered.
          RoundedImageLabel paints the rounded #222222 background.
        """
        target = QPixmap(40, 40)
        target.fill(Qt.transparent)

        if self.cover_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(self.cover_data) and not pixmap.isNull():
                return pixmap.scaled(
                    40, 40,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )

        icon_size = 24
        icon_pixmap = FIF.MUSIC.icon(Theme.DARK).pixmap(icon_size, icon_size)

        if not icon_pixmap.isNull():
            painter = QPainter(target)
            painter.setRenderHints(
                QPainter.Antialiasing | QPainter.SmoothPixmapTransform
            )
            x = (40 - icon_size) // 2
            y = (40 - icon_size) // 2
            painter.drawPixmap(x, y, icon_pixmap)
            painter.end()

        return target

    def __on_clicked(self):
        self.itemClicked.emit(self.file_name)

    def enterEvent(self, event):
        super().enterEvent(event)
        if self._blurred_pixmap is None:
            self._blurred_pixmap = blur_pixmap(self._original_pixmap, radius=6)
        if self._blurred_pixmap and not self._blurred_pixmap.isNull():
            self.cover_label.setPixmap(self._blurred_pixmap)
        play_pixmap = FIF.PLAY.icon(Theme.DARK).pixmap(20, 20)
        self.play_icon_label.setPixmap(play_pixmap)
        self.play_icon_label.show()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.play_icon_label.hide()
        if self._original_pixmap and not self._original_pixmap.isNull():
            self.cover_label.setPixmap(self._original_pixmap)