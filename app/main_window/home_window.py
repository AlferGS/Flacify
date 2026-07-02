#main_window/home_window.py
from pathlib import Path

from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from qfluentwidgets import ScrollArea

from app.components import FileListItem, PlayerBar
from app.core import AudioPlayerController, FileBrowserModel


# Home application page
class HomeWindow(QWidget):
    def __init__(self, file_browser: FileBrowserModel, audio_player: AudioPlayerController, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeWindow") 
        self.setAutoFillBackground(True)
        self.file_browser = file_browser
        self.__init_ui(audio_player)

    def __init_ui(self, audio_player:AudioPlayerController) -> None:
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

        # Подключаем сигнал изменения директории к перерисовке
        self.file_browser.directoryChanged.connect(self._load_dir)
        self._load_dir() # Первичная загрузка

        self.player_bar = PlayerBar(audio_player)
        self.main_vert_layout.addWidget(self.player_bar)


    def _load_dir(self):
        items = self.file_browser.current_dir
        self._render_items(items)


    def _render_items(self, items: dict[int, Path]):
        # Очистка текущего layout
        while self.view_layout.count():
            item = self.view_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Кнопка "Назад" [..], если мы не в корневой папке
        if self.file_browser.current_pos != self.file_browser.root_path:
            prev_item = FileListItem("[..]", True)
            prev_item.itemClicked.connect(self.file_browser.back_previous_dir)
            self.view_layout.addWidget(prev_item)

        # Рендер файлов и папок
        for key, filename in items.items():
            full_path = self.file_browser.current_pos / filename
            if not full_path.exists():
                continue

            file_item = FileListItem(full_path.name, full_path.is_dir())
            
            file_item.itemClicked.connect(self.file_browser.handle_item_click)
            self.view_layout.addWidget(file_item)

        self.view_layout.addStretch(1)
