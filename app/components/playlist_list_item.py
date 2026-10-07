#components/playlist_list_item.py
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import CardWidget

from app.components.playlist_badge import PlaylistBadge
from app.core.playlist import Playlist


class PlaylistListItem(CardWidget):
    """
    Playlist row: badge + title + track count.
    Similar to FolderListItem, but with a PlaylistBadge.
    """

    itemClicked = pyqtSignal(str)  # playlist_id
    contextMenuRequested = pyqtSignal(str, object)  # (playlist_id, QPoint)

    def __init__(self, playlist: Playlist, parent=None):
        super().__init__(parent)
        self._playlist = playlist
        self._is_hovered = False
        self.setFixedHeight(56)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)

        self._badge = PlaylistBadge(
            initials=playlist.get_initials(),
            color=playlist.color,
            size=40,
        )
        layout.addWidget(self._badge)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self._name_label = QLabel(playlist.name)
        self._name_label.setStyleSheet(
            "color: #FFFFFF; font-size: 14px; font-weight: 500;"
        )

        track_count = len(playlist.tracks)
        word = "track" if track_count == 1 else "tracks"
        self._count_label = QLabel(f"{track_count} {word}")
        self._count_label.setStyleSheet("color: #888888; font-size: 11px;")

        text_layout.addWidget(self._name_label)
        text_layout.addWidget(self._count_label)
        layout.addLayout(text_layout, stretch=1)

        self._apply_background()

    # Update

    def update_playlist(self, playlist: Playlist) -> None:
        """Refresh the display when the playlist changes."""
        self._playlist = playlist
        self._badge.set_initials(playlist.get_initials())
        self._badge.set_color(playlist.color)
        self._name_label.setText(playlist.name)
        track_count = len(playlist.tracks)
        word = "track" if track_count == 1 else "tracks"
        self._count_label.setText(f"{track_count} {word}")

    # Mouse events

    def enterEvent(self, event):
        self._is_hovered = True
        self._apply_background()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._apply_background()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.itemClicked.emit(self._playlist.id)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        self.contextMenuRequested.emit(self._playlist.id, event.globalPos())
        event.accept()

    # Protected

    def _apply_background(self) -> None:
        bg = "#1F1F1F" if self._is_hovered else "#111111"
        self.setStyleSheet(
            f"PlaylistListItem {{ background: {bg}; border-radius: 10px; border: none; }}"
        )