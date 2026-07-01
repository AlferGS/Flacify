from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,QHBoxLayout,
    QLabel,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor
from qfluentwidgets import (
    PushButton, 
    CardWidget,
    IconWidget,
    BodyLabel,
    ScrollArea,
    FluentIcon as FIF
)
from app.components import PlayerBar #, FileListItem
from app.core import FileBrowserModel
from app.core import AudioPlayerController


class FileListItem(CardWidget):
    """ Class for elements in view layout
    """
    itemClicked = pyqtSignal(str)
    def __init__(self, filename: str, is_dir: bool=False, parent=None):
        super().__init__(parent)
        self.filename = filename 
        self.setFixedHeight(46)
        self.setStyleSheet("background: transparent; color: #111111")

        # Create main layout
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(13,13,13,13)

        # Set icon
        self.icon = IconWidget()
        self.icon.setIcon(FIF.MUSIC_FOLDER if is_dir else FIF.MUSIC)
        self.icon.setFixedSize(20,20)

        # Filename label
        self.label = BodyLabel(self.filename)
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # Add element in layout
        self.h_layout.addWidget(self.icon)
        self.h_layout.addSpacing(5)
        self.h_layout.addWidget(self.label)
        self.h_layout.addStretch(1)

        self.clicked.connect(self._on_clicked)

    
    def _on_clicked(self):
        self.itemClicked.emit(self.filename)


# Home application page
class HomeWindow(QWidget):
    def __init__(self, file_browser: FileBrowserModel, audio_player: AudioPlayerController, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeWindow") 
        self.file_browser = file_browser
        self.__init_ui(audio_player)


    def __init_ui(self, audio_player:AudioPlayerController) -> None:
        main_vert_layout = QVBoxLayout(self)
        # main_vert_layout.setContentsMargins(15, 5, 15, 5)
        main_vert_layout.setContentsMargins(0, 5, 0, 0)
        
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        
        self.view_container = QWidget()
        self.view_layout = QVBoxLayout(self.view_container)
        self.view_layout.setContentsMargins(16, 16, 16, 16)
        self.view_layout.setSpacing(8)
        
        self.scroll_area.setWidget(self.view_container)
        main_vert_layout.addWidget(self.scroll_area)

        # Подключаем сигнал изменения директории к перерисовке
        self.file_browser.directoryChanged.connect(self._load_dir)
        self._load_dir() # Первичная загрузка

        self.player_bar = PlayerBar(audio_player)


        # main_vert_layout.addSpacing(10)
        main_vert_layout.addWidget(self.player_bar)


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

            is_dir = full_path.is_dir()
            file_item = FileListItem(full_path.name, is_dir)
            
            file_item.itemClicked.connect(self.file_browser.handle_item_click)
            self.view_layout.addWidget(file_item)

        self.view_layout.addStretch(1)


    def paintEvent(self, event):
        """ Override paintEvent to forced painting black background """
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#111111"))
        painter.end()