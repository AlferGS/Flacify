#windows/playlist_detail_window.py
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QAction,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    FluentIcon,
    PushButton,
    ScrollArea,
    SubtitleLabel,
    CaptionLabel,
)

from app.components.playlist_badge import PlaylistBadge
from app.components.queue_track_item import QueueTrackItem
from app.core.playlist import Playlist
# from app.core.metadata_reader import MetadataReader


class PlaylistDetailWindow(QWidget):
    """
    Page displaying tracks from a single playlist.
    Supports: playback, removal from the playlist,
    adding tracks, a context menu, and drag-and-drop reordering.
    """

    play_track_requested = pyqtSignal(Path, list)      # (path, all_paths)
    back_requested = pyqtSignal()
    add_tracks_confirmed = pyqtSignal(str, list)       # (playlist_id, [Path])
    remove_track_requested = pyqtSignal(str, int)      # (playlist_id, track_index)
    add_to_playlist_requested = pyqtSignal(Path, object)  # (path, QPoint)
    reorder_requested = pyqtSignal(str, int, int)      # (playlist_id, from, to)

    AUDIO_EXTENSIONS = {".flac", ".mp3", ".wav", ".ogg", ".aac", ".m4a", ".wma"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PlaylistDetailWindow")
        self._playlist: Optional[Playlist] = None
        self._track_items: list[QueueTrackItem] = []

        self._setup_ui()

    # UI

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        # "Back" button
        self._back_btn = PushButton(FluentIcon.LEFT_ARROW, "")
        self._back_btn.setFixedSize(36, 36)
        self._back_btn.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(self._back_btn)

        # playlist badge (large)
        self._badge = PlaylistBadge(initials="", color="#1DB954", size=64)
        header_layout.addWidget(self._badge)

        # name + quantity
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self._name_label = SubtitleLabel("")
        self._name_label.setStyleSheet("color: #FFFFFF;")
        info_layout.addWidget(self._name_label)

        self._count_label = CaptionLabel("")
        self._count_label.setStyleSheet("color: #888888;")
        info_layout.addWidget(self._count_label)

        header_layout.addLayout(info_layout, stretch=1)

        # "Add tracks" button
        self._add_btn = PushButton(FluentIcon.ADD, "Add tracks")
        self._add_btn.setFixedHeight(36)
        self._add_btn.clicked.connect(self._on_add_tracks_clicked)
        header_layout.addWidget(self._add_btn)

        main_layout.addLayout(header_layout)

        # tracks list
        self._scroll_area = ScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet(
            "ScrollArea { background: #111111; border: none; border-radius: 10px; }"
        )

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: #111111;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(4, 4, 4, 4)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()

        self._scroll_area.setWidget(self._list_widget)
        main_layout.addWidget(self._scroll_area, stretch=1)

        self._empty_label = QLabel("The playlist is empty.\nClick  «Add tracks».")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("color: #666666; font-size: 14px;")
        self._empty_label.setVisible(False)
        main_layout.addWidget(self._empty_label)

    # Public methods

    def set_playlist(self, playlist: Playlist) -> None:
        """Load and display the playlist."""
        self._playlist = playlist

        # Header
        self._badge.set_initials(playlist.get_initials())
        self._badge.set_color(playlist.color)
        self._name_label.setText(playlist.name)

        track_count = len(playlist.tracks)
        word = "track" if track_count == 1 else "tracks"
        self._count_label.setText(f"{track_count} {word}")

        self._rebuild_track_list()

    def set_app_state(self, app_state) -> None:
        """Store reference to AppState for highlight logic."""
        self._app_state = app_state

    def highlight_current_track(self, *args) -> None:
        """Highlight the currently playing track.
        Connected to trackChanged(title, artist, album, cover_data)."""
        if not hasattr(self, '_app_state') or self._app_state is None:
            return
        current = self._app_state.current_track_path
        for item in self._track_items:
            old = item.is_current
            item.is_current = (item.track_path == current)
            if old != item.is_current:
                item._update_text_colors()
                item.update()

    # Protected

    def _rebuild_track_list(self) -> None:
        """Recreate the tracklist from the playlist data."""
        for item in self._track_items:
            self._list_layout.removeWidget(item)
            item.deleteLater()
        self._track_items.clear()

        if self._playlist is None:
            return

        tracks = self._playlist.tracks
        has_tracks = len(tracks) > 0
        self._empty_label.setVisible(not has_tracks)
        self._scroll_area.setVisible(has_tracks)

        for idx, track in enumerate(tracks):
            item = QueueTrackItem(
                track_path=track.path,
                is_current=False,
            )
            item.track_single_clicked.connect(self._on_track_single_clicked)
            item.context_menu_requested.connect(self._on_track_context_menu)
            self._track_items.append(item)
            self._list_layout.insertWidget(self._list_layout.count() - 1, item)

    def _on_track_single_clicked(self, path: Path) -> None:
        """Double-click — play track."""
        if self._playlist:
            all_paths = self._playlist.track_paths
            self.play_track_requested.emit(path, all_paths)

    def _on_track_context_menu(self, path: Path, pos) -> None:
        """Track context menu in the playlist."""
        if self._playlist is None:
            return

        # find track index
        track_index = None
        for i, t in enumerate(self._playlist.tracks):
            if t.path == path:
                track_index = i
                break

        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #1F1F1F; border: 1px solid #333; border-radius: 8px; }"
            "QMenu::item { color: #FFF; padding: 6px 24px; }"
            "QMenu::item:selected { background: #2A2A2A; }"
        )

        add_action = QAction("Add to playlist", self)
        add_action.triggered.connect(lambda: self.add_to_playlist_requested.emit(path, pos))
        menu.addAction(add_action)

        if track_index is not None:
            remove_action = QAction("Delete from this playlist", self)
            remove_action.triggered.connect(
                lambda: self.remove_track_requested.emit(self._playlist.id, track_index)
            )
            menu.addAction(remove_action)

        menu.exec_(pos)

    def _on_back_clicked(self) -> None:
        self.back_requested.emit()

    def _on_add_tracks_clicked(self) -> None:
        """Open the file dialog to add tracks."""
        extensions = " ".join(f"*{ext}" for ext in sorted(self.AUDIO_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add tracks in playlist",
            "",
            f"Audiofiles ({extensions})",
        )
        if files and self._playlist:
            paths = [Path(f) for f in files]
            self.add_tracks_confirmed.emit(self._playlist.id, paths)