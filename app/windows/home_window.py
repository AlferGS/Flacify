#windows/home_window.py
from pathlib import Path

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget

from qfluentwidgets import ScrollArea

from app.components import FolderListItem, SongListItem, PlayerBar, QueueWindow
from app.core.app_state import AppState

class HomeWindow(QWidget):
    """Home application page"""
    itemClicked = pyqtSignal(Path)
    backRequested = pyqtSignal()
    requestDirectory = pyqtSignal()

    def __init__(self, app_state: AppState, parent=None):
        """Init event.
        Set HomeWindow default settings and init ui.
        """
        super().__init__(parent)
        self.setObjectName("HomeWindow") 
        self.setAutoFillBackground(True)
        self.app_state = app_state
        self.__init_ui(app_state)


    def __init_ui(self, app_state:AppState) -> None:
        # Main vertical box for main_horiz_layout and PlayerBar
        self.main_vert_layout = QVBoxLayout(self)
        self.main_vert_layout.setContentsMargins(0, 0, 0, 0)
        self.main_vert_layout.setSpacing(0)
        # Main horizontal box for ScrollArea and QueueWindow
        self.main_container = QWidget()
        self.main_container.setContentsMargins(8, 8, 8, 8)
        self.main_container.setStyleSheet("background: #000000; border: none;")

        self.main_horiz_layout = QHBoxLayout()
        self.main_horiz_layout.setContentsMargins(0, 0, 0, 0)
        self.main_horiz_layout.setSpacing(0)
        self.main_container.setLayout(self.main_horiz_layout)
        # Scroll box for file list items
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
                    cover_data=meta.get("cover_data")
                )

            list_item.itemClicked.connect(lambda checked, p=full_path: self.itemClicked.emit(p))
            self.view_layout.addWidget(list_item)

        self.view_layout.addStretch(1)


    def _onDirectoryLoaded(self, payload: dict):
        """Render the new item list after a directory scan completes."""
        self.__render_items(payload)
