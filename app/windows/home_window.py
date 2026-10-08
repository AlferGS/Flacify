#windows/home_window.py
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QMenu, QAction, QFrame

from qfluentwidgets import (
    ScrollArea, FluentIcon, PushButton, SubtitleLabel, CaptionLabel,
    TransparentToolButton,
)

from app.components import FolderListItem, SongListItem, PlayerBar, QueueWindow
from app.components.playlist_track_container import PlaylistTrackContainer
from app.components.playlist_badge import PlaylistBadge
from app.components.round_tool_button import RoundToolButton
from app.core.app_state import AppState
from app.core.metadata_reader import MetadataReader
from app.core.playlist import Playlist


class HomeWindow(QWidget):
    """Home application page. Two modes: file browser and playlist view."""

    # Browser signals
    itemClicked = pyqtSignal(Path)
    backRequested = pyqtSignal()
    requestDirectory = pyqtSignal()
    add_to_playlist_requested = pyqtSignal(Path, object)

    # Playlist signals
    playlist_track_clicked = pyqtSignal(int, list)          # (track_index, all_paths)
    playlist_remove_track_requested = pyqtSignal(str, int)  # (playlist_id, track_index)
    playlist_add_tracks_requested = pyqtSignal(str)         # playlist_id
    playlist_play_requested = pyqtSignal(str)               # playlist_id
    playlist_shuffle_requested = pyqtSignal(str)            # playlist_id
    playlist_edit_requested = pyqtSignal(str)               # playlist_id
    playlist_delete_requested = pyqtSignal(str)             # playlist_id
    playlist_reorder_requested = pyqtSignal(str, int, int)  # (playlist_id, from, to)

    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeWindow")
        self.setAutoFillBackground(True)
        self.app_state = app_state
        self._current_mode = "browser"
        self._current_playlist: Optional[Playlist] = None
        self._playlist_track_items: list[SongListItem] = []
        self._track_container = None
        self.__init_ui(app_state)

    def __init_ui(self, app_state: AppState) -> None:
        self.main_vert_layout = QVBoxLayout(self)
        self.main_vert_layout.setContentsMargins(0, 0, 0, 0)
        self.main_vert_layout.setSpacing(0)

        self.main_container = QWidget()
        self.main_container.setAttribute(Qt.WA_StyledBackground, True)
        self.main_container.setContentsMargins(8, 8, 8, 8)
        self.main_container.setStyleSheet("background: #000000; border: none;")
        self.main_horiz_layout = QHBoxLayout()
        self.main_horiz_layout.setContentsMargins(0, 0, 0, 0)
        self.main_horiz_layout.setSpacing(0)
        self.main_container.setLayout(self.main_horiz_layout)

        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setViewportMargins(0, 0, 0, 0)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #111111;
                border-radius: 10px;
                border: none;
            }
            QScrollArea::viewport {
                background-color: transparent;
                border: none;
            }
        """)

        self.scroll_container = QWidget()
        self.scroll_container.setStyleSheet("background: transparent; border: none;")
        self.view_layout = QVBoxLayout(self.scroll_container)
        self.view_layout.setContentsMargins(16, 16, 16, 16)
        self.view_layout.setSpacing(8)

        self.queue_window = QueueWindow(self.app_state)
        self.queue_window.setFixedWidth(250)

        self.scroll_area.setWidget(self.scroll_container)
        self.main_horiz_layout.addWidget(self.scroll_area, stretch=1)
        self.main_horiz_layout.addSpacing(8)
        self.main_horiz_layout.addWidget(self.queue_window, stretch=0)

        self.main_vert_layout.addWidget(self.main_container)

        self.player_bar = PlayerBar(app_state)
        self.main_vert_layout.addWidget(self.player_bar)

    # ==================== Browser mode ====================

    def show_browser(self) -> None:
        """Switch to file browser mode and rescan current directory."""
        self._current_mode = "browser"
        self._current_playlist = None
        self._clear_view_layout()
        self.requestDirectory.emit()

    def __render_items(self, payload: dict):
        """Clear current layout and render new files/folders from a scan payload."""
        while self.view_layout.count():
            item = self.view_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if self.app_state.current_library_path != self.app_state.root_path:
            prev_item = FolderListItem("[..]")
            prev_item.itemClicked.connect(self.backRequested.emit)
            self.view_layout.addWidget(prev_item)

        items = payload.get("items", [])
        metadata_map = payload.get("metadata", {})

        for full_path in items:
            if not full_path.exists():
                continue
            if full_path.is_dir():
                list_item = FolderListItem(full_path.name)
            else:
                meta = metadata_map.get(full_path, {})
                list_item = SongListItem(
                    file_name=full_path.name,
                    song_name=meta.get("title", full_path.stem),
                    artist=meta.get("artist", "Unknown Artist"),
                    song_dur=meta.get("song_dur", "00:00"),
                    cover_data=meta.get("cover_data"),
                    track_path=full_path,
                )
                list_item.context_menu_requested.connect(
                    lambda pos, p=full_path: self.add_to_playlist_requested.emit(p, pos)
                )
            list_item.itemClicked.connect(lambda checked, p=full_path: self.itemClicked.emit(p))
            self.view_layout.addWidget(list_item)
        self.view_layout.addStretch(1)

    def _onDirectoryLoaded(self, payload: dict):
        """Render the new item list after a directory scan completes."""
        if self._current_mode == "playlist":
            return
        self._current_mode = "browser"
        self.__render_items(payload)

    # ==================== Playlist mode ====================

    def show_playlist(self, playlist: Playlist) -> None:
        """Switch to playlist view mode."""
        self._current_mode = "playlist"
        self._current_playlist = playlist
        self._clear_view_layout()
        self.__render_playlist_header(playlist)
        self.__render_playlist_tracks(playlist)

    def is_showing_playlist(self, playlist_id: str) -> bool:
        """True if HomeWindow currently displays this playlist."""
        return (
            self._current_mode == "playlist"
            and self._current_playlist is not None
            and self._current_playlist.id == playlist_id
        )

    def reset_to_browser_if_playlist(self) -> bool:
        """If currently showing a playlist, switch back to browser mode.
        Returns True if the mode was actually changed (caller may rely on it)."""
        if self._current_mode == "playlist":
            self.show_browser()
            return True
        return False

    def update_playlist_view(self, playlist: Playlist) -> None:
        """Refresh playlist view if this playlist is currently displayed."""
        if self._current_mode == "playlist" and self._current_playlist and \
           self._current_playlist.id == playlist.id:
            self.show_playlist(playlist)

    def highlight_playlist_track(self, *args) -> None:
        """Highlight the currently playing track in playlist mode (duplicate-safe)."""
        if self._current_mode != "playlist":
            return
        highlight_idx = self.__current_display_index()
        for i, item in enumerate(self._playlist_track_items):
            item._set_current(i == highlight_idx)

    def __current_display_index(self) -> int:
        """Map the current queue position to a displayed row index.
        Duplicates are resolved by occurrence rank: the n-th equal path
        in the queue maps to the n-th equal path in the displayed list."""
        queue = self.app_state.playlist_paths
        idx = self.app_state.current_track_index
        if not queue or idx < 0 or idx >= len(queue):
            return -1
        current_path = queue[idx]
        rank = sum(1 for i in range(idx) if queue[i] == current_path)
        seen = 0
        for i, item in enumerate(self._playlist_track_items):
            if item.track_path == current_path:
                if seen == rank:
                    return i
                seen += 1
        return -1

    # ==================== Protected ====================

    def _clear_view_layout(self) -> None:
        """Remove all widgets and nested layouts from view_layout."""
        while self.view_layout.count():
            item = self.view_layout.takeAt(0)
            self._delete_layout_item(item)
        self._playlist_track_items.clear()

    def _delete_layout_item(self, item) -> None:
        """Recursively delete a layout item: widget or nested layout."""
        widget = item.widget()
        if widget:
            widget.setParent(None)
            widget.deleteLater()
            return
        layout = item.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                self._delete_layout_item(child)

    def __render_playlist_header(self, playlist: Playlist) -> None:
        """Spotify-like header: badge+info row, controls row, divider."""
        # --- Row 1: badge + info ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        badge = PlaylistBadge(
            initials=playlist.get_initials(),
            color=playlist.color,
            size=96,
        )
        header_layout.addWidget(badge)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        caption = CaptionLabel("Playlist")
        caption.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        info_layout.addWidget(caption)

        name_label = SubtitleLabel(playlist.name)
        name_label.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: bold;")
        info_layout.addWidget(name_label)

        track_count = len(playlist.tracks)
        word = "track" if track_count == 1 else "tracks"
        count_label = CaptionLabel(f"{track_count} {word}")
        count_label.setStyleSheet("color: #AAAAAA;")
        info_layout.addWidget(count_label)

        info_layout.addStretch(1)
        header_layout.addLayout(info_layout, stretch=1)

        self.view_layout.addLayout(header_layout)
        self.view_layout.addSpacing(12)

        # --- Row 2: controls ---
        controls = QHBoxLayout()
        controls.setSpacing(10)

        back_btn = TransparentToolButton(FluentIcon.LEFT_ARROW)
        back_btn.setFixedSize(36, 36)
        back_btn.clicked.connect(self.show_browser)
        controls.addWidget(back_btn)

        play_btn = RoundToolButton(FluentIcon.PLAY, size=44)
        play_btn.clicked.connect(lambda: self.playlist_play_requested.emit(playlist.id))
        controls.addWidget(play_btn)

        shuffle_btn = TransparentToolButton(FluentIcon.SYNC)
        shuffle_btn.setFixedSize(36, 36)
        shuffle_btn.clicked.connect(lambda: self.playlist_shuffle_requested.emit(playlist.id))
        controls.addWidget(shuffle_btn)

        more_btn = TransparentToolButton(FluentIcon.MORE)
        more_btn.setFixedSize(36, 36)
        more_btn.clicked.connect(lambda: self.__on_playlist_more_clicked(playlist.id))
        controls.addWidget(more_btn)

        controls.addStretch(1)

        add_btn = PushButton(FluentIcon.ADD, "Add tracks")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(
            lambda: self.playlist_add_tracks_requested.emit(playlist.id)
        )
        controls.addWidget(add_btn)

        self.view_layout.addLayout(controls)
        self.view_layout.addSpacing(8)

        # --- Divider ---
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #2A2A2A; border: none;")
        self.view_layout.addWidget(divider)
        self.view_layout.addSpacing(8)

    def __render_playlist_tracks(self, playlist: Playlist) -> None:
        """Render playlist tracks as SongListItem rows inside a drag&drop container."""
        items = []
        for track_index, track in enumerate(playlist.tracks):
            meta = MetadataReader.get_metadata(track.path)
            item = SongListItem(
                file_name=track.path.name,
                song_name=meta.get("title", track.path.stem),
                artist=meta.get("artist", "Unknown Artist"),
                song_dur=meta.get("song_dur", "00:00"),
                cover_data=meta.get("cover_data"),
                is_current=False,
                track_path=track.path,
                drag_enabled=True,
            )
            item.itemClicked.connect(
                lambda _, idx=track_index: self._on_playlist_track_clicked(idx)
            )
            item.context_menu_requested.connect(
                lambda pos, idx=track_index: self._on_playlist_track_context_menu(idx, pos)
            )
            items.append(item)

        self._playlist_track_items = items
        self._track_container = PlaylistTrackContainer(self)
        self._track_container.set_items(items)
        self._track_container.order_changed.connect(
            lambda f, t: self.playlist_reorder_requested.emit(playlist.id, f, t)
        )
        self.view_layout.addWidget(self._track_container)
        self.view_layout.addStretch(1)
        # Apply highlight by queue position (duplicate-safe)
        self.highlight_playlist_track()

    def __on_playlist_more_clicked(self, playlist_id: str) -> None:
        """'...' button: rename / delete playlist."""
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #1F1F1F; border: 1px solid #333; border-radius: 8px; }"
            "QMenu::item { color: #FFF; padding: 6px 24px; }"
            "QMenu::item:selected { background: #2A2A2A; }"
        )
        edit_action = QAction("Rename", self)
        edit_action.triggered.connect(
            lambda: self.playlist_edit_requested.emit(playlist_id)
        )
        menu.addAction(edit_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(
            lambda: self.playlist_delete_requested.emit(playlist_id)
        )
        menu.addAction(delete_action)

        menu.exec_(QCursor.pos())

    def _on_playlist_track_clicked(self, track_index: int) -> None:
        """Single click on a playlist track — request playback by position."""
        if self._current_playlist:
            all_paths = self._current_playlist.track_paths
            self.playlist_track_clicked.emit(track_index, all_paths)

    def _on_playlist_track_context_menu(self, track_index: int, pos) -> None:
        """Context menu: add to playlist / remove from this playlist by row index."""
        if self._current_playlist is None:
            return
        if not (0 <= track_index < len(self._current_playlist.tracks)):
            return

        path = self._current_playlist.tracks[track_index].path

        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #1F1F1F; border: 1px solid #333; border-radius: 8px; }"
            "QMenu::item { color: #FFF; padding: 6px 24px; }"
            "QMenu::item:selected { background: #2A2A2A; }"
        )

        add_action = QAction("Add to playlist", self)
        add_action.triggered.connect(
            lambda: self.add_to_playlist_requested.emit(path, pos)
        )
        menu.addAction(add_action)

        remove_action = QAction("Remove from this playlist", self)
        remove_action.triggered.connect(
            lambda: self.playlist_remove_track_requested.emit(
                self._current_playlist.id, track_index
            )
        )
        menu.addAction(remove_action)

        menu.exec_(pos)