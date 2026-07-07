#main_window/home_window.py
from pathlib import Path

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from qfluentwidgets import ScrollArea

from app.components import FolderListItem, SongListItem, PlayerBar
from app.core import MetadataReader
from app.core.app_state import AppState

# Home application page
class HomeWindow(QWidget):
    itemClicked = pyqtSignal(Path)
    backRequested = pyqtSignal()
    requestDirectory = pyqtSignal()

    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeWindow") 
        self.setAutoFillBackground(True)
        self.app_state = app_state
        self.__init_ui(app_state)

    def __init_ui(self, app_state:AppState) -> None:
        # Main vertical box for ScrollArea and playerBar
        self.main_vert_layout = QVBoxLayout(self)
        self.main_vert_layout.setContentsMargins(0, 0, 0, 0)
        self.main_vert_layout.setSpacing(0)
        # Scroll box for file list items
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
        ScrollArea {
            background: #111111;
        }
        """)
        
        self.view_container = QWidget()
        self.view_container.setStyleSheet("background: #111111; border: none;")

        self.view_layout = QVBoxLayout(self.view_container)
        self.view_layout.setContentsMargins(16, 16, 16, 16)
        self.view_layout.setSpacing(8)
        
        self.scroll_area.setWidget(self.view_container)
        self.main_vert_layout.addWidget(self.scroll_area)

        self.player_bar = PlayerBar(app_state)
        self.main_vert_layout.addWidget(self.player_bar)


    def onDirectoryLoaded(self, items: list[Path]):
        """Слот для получения списка файлов от FileBrowserModel"""
        self._render_items(items)

    def _render_items(self, items: list[Path]):
        # Очистка текущего layout
        while self.view_layout.count():
            item = self.view_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Кнопка "Назад" [..], если мы не в корневой папке
        if self.app_state.current_library_path != self.app_state.root_path:
            prev_item = FolderListItem("[..]")
            prev_item.itemClicked.connect(self.backRequested.emit)
            self.view_layout.addWidget(prev_item)

        # Рендер файлов и папок
        for full_path in items:
            if not full_path.exists():
                continue
            
            if full_path.is_dir():
                list_item = FolderListItem(full_path.name)
            else:
                meta = MetadataReader.get_metadata(full_path)
                list_item = SongListItem(
                    file_name=full_path.name,
                    song_name=meta.get('title', full_path.stem),
                    artist=meta.get('artist', 'Unknown Artist'),
                    song_dur=meta.get('song_dur', '00:00'),
                    cover_data=meta.get('cover_data')
                )
            
            # Эмитим сигнал с путем при клике
            list_item.itemClicked.connect(lambda checked, p=full_path: self.itemClicked.emit(p))
            self.view_layout.addWidget(list_item)

        self.view_layout.addStretch(1)
