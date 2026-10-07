#windows/playlists_window.py
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    FluentIcon,
    PushButton,
    ScrollArea,
    SubtitleLabel,
)

from app.components.playlist_list_item import PlaylistListItem
from app.core.playlist import Playlist


class PlaylistsWindow(QWidget):
    """
    A page listing all of a user's playlists.
    Displays a badge, name, and track count for each playlist.
    """

    playlist_selected = pyqtSignal(str)       # playlist_id
    create_playlist_requested = pyqtSignal()
    edit_playlist_requested = pyqtSignal(str)  # playlist_id (context menu)
    delete_playlist_requested = pyqtSignal(str)  # playlist_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PlaylistsWindow")
        self._items: dict[str, PlaylistListItem] = {}

        self._setup_ui()

    # UI

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)


        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self._title_label = SubtitleLabel("My playlists")
        self._title_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(self._title_label)

        header_layout.addStretch()

        self._create_btn = PushButton(FluentIcon.ADD, "Create")
        self._create_btn.setFixedHeight(36)
        self._create_btn.clicked.connect(self.create_playlist_requested.emit)
        header_layout.addWidget(self._create_btn)

        main_layout.addLayout(header_layout)

        # Scroll area with list
        self._scroll_area = ScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet(
            "ScrollArea { background: #111111; border: none; border-radius: 10px; }"
        )

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: #111111;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(4, 4, 4, 4)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        self._scroll_area.setWidget(self._list_widget)
        main_layout.addWidget(self._scroll_area, stretch=1)

        self._empty_label = QLabel("No playlists. Tap «Create» to get started.")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("color: #666666; font-size: 14px;")
        self._empty_label.setVisible(True)
        main_layout.addWidget(self._empty_label)

    # Public methods

    def set_playlists(self, playlists: list[Playlist]) -> None:
        """Completely rebuild the playlist list."""
        # Clear
        for item in self._items.values():
            self._list_layout.removeWidget(item)
            item.deleteLater()
        self._items.clear()

        for playlist in playlists:
            item = PlaylistListItem(playlist)
            item.itemClicked.connect(self._on_item_clicked)
            item.contextMenuRequested.connect(self._on_item_context_menu)
            self._items[playlist.id] = item
            
            self._list_layout.insertWidget(self._list_layout.count() - 1, item)

        has_playlists = len(playlists) > 0
        self._empty_label.setVisible(not has_playlists)
        self._scroll_area.setVisible(has_playlists)

    # Protected

    def _on_item_clicked(self, playlist_id: str) -> None:
        self.playlist_selected.emit(playlist_id)

    def _on_item_context_menu(self, playlist_id: str, pos) -> None:
        from PyQt5.QtWidgets import QMenu, QAction

        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #1F1F1F; border: 1px solid #333; border-radius: 8px; }"
            "QMenu::item { color: #FFF; padding: 6px 24px; }"
            "QMenu::item:selected { background: #2A2A2A; }"
        )

        edit_action = QAction("Rename", self)
        edit_action.triggered.connect(lambda: self.edit_playlist_requested.emit(playlist_id))
        menu.addAction(edit_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_playlist_requested.emit(playlist_id))
        menu.addAction(delete_action)

        menu.exec_(pos)