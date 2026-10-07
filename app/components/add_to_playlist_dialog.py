#components/add_to_playlist_dialog.py
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CheckBox,
    MessageBoxBase,
    PushButton,
    ScrollArea,
    SubtitleLabel,
)

from app.components.playlist_badge import PlaylistBadge
from app.core.playlist import Playlist


class PlaylistCheckRow(QWidget):
    """Single line: checkbox + badge + playlist name."""

    def __init__(self, playlist: Playlist, parent=None):
        super().__init__(parent)
        self.playlist_id = playlist.id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)

        self.checkbox = CheckBox()
        self.checkbox.setChecked(False)
        layout.addWidget(self.checkbox)

        badge = PlaylistBadge(
            initials=playlist.get_initials(),
            color=playlist.color,
            size=28,
        )
        layout.addWidget(badge)

        name_label = QLabel(playlist.name)
        name_label.setStyleSheet("color: #FFFFFF; font-size: 13px;")
        layout.addWidget(name_label, stretch=1)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()


class AddToPlaylistDialog(MessageBoxBase):
    """
    Playlist selection dialog for adding tracks.
    Allows selecting multiple playlists using checkboxes.
    """

    confirmed = pyqtSignal(list)  # list[str] playlist_ids

    def __init__(self, playlists: list[Playlist], parent=None):
        super().__init__(parent)
        self._rows: list[PlaylistCheckRow] = []

        self.titleLabel = SubtitleLabel("Add to playlist", self)
        self.titleLabel.setContentsMargins(0, 0, 0, 12)

        # Scroll area for all playlists
        self._scroll_area = ScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFixedHeight(min(300, max(100, len(playlists) * 44)))
        self._scroll_area.setStyleSheet(
            "ScrollArea { background: transparent; border: none; }"
        )

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setSpacing(2)
        self._list_layout.setContentsMargins(0, 0, 0, 0)

        for playlist in playlists:
            row = PlaylistCheckRow(playlist)
            self._rows.append(row)
            self._list_layout.addWidget(row)

        self._list_layout.addStretch()
        self._scroll_area.setWidget(self._list_widget)

        # "New playlist" Button
        self._new_playlist_btn = PushButton("+ New playlist", self)
        self._new_playlist_btn.setStyleSheet(
            "PushButton { background: transparent; color: #1DB954; "
            "border: none; font-size: 13px; }"
            "PushButton:hover { color: #1ed760; }"
        )
        self._new_playlist_btn.clicked.connect(self._on_new_playlist)

        self.yesButton.setText("Add track")
        self.cancelButton.setText("Cancel")

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self._scroll_area)
        self.viewLayout.addWidget(self._new_playlist_btn)
        self.viewLayout.addSpacing(8)

        self.yesButton.clicked.connect(self._on_confirm)

        self.widget.setMinimumWidth(360)

    # Signals

    new_playlist_requested = pyqtSignal()

    # Protected

    def _on_new_playlist(self) -> None:
        self.new_playlist_requested.emit()

    def _on_confirm(self) -> None:
        selected_ids = [row.playlist_id for row in self._rows if row.is_checked()]
        if selected_ids:
            self.confirmed.emit(selected_ids)
        self.accept()

    def refresh_playlists(self, playlists: list[Playlist]) -> None:
        """Update list (after creating/deleting new/old playlist)."""
        # Clear area
        for row in self._rows:
            self._list_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()

        # Recreate list
        for playlist in playlists:
            row = PlaylistCheckRow(playlist)
            self._rows.append(row)
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)