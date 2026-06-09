from pathlib import Path
import sys
from qfluentwidgets import (
    FluentWindow, 
    setTheme,
    Theme,
    ListWidget, TreeWidget, ScrollArea, VBoxLayout, 
    PushButton, EditableComboBox, CheckBox, CardWidget, IconWidget, BodyLabel, SubtitleLabel,
    NavigationItemPosition, NavigationInterface,
    FluentIcon as FIF
)
from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QFrame, 
    QLabel, 
    QVBoxLayout, 
    QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from FileBrowserModel import FileBrowserModel

class FileListItem(CardWidget):
    itemClicked = pyqtSignal(str)

    """Один элемент в списке (папка или файл)"""
    def __init__(self, filename: str, is_dir:bool=False, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.setFixedHeight(60) # Фиксированная высота для единообразия
        
        # Layout внутри карточки
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(16, 10, 16, 10)
        
        # Иконка (можно менять в зависимости от того, файл это или папка)
        self.icon = IconWidget()
        # Здесь можно поставить условную логику: если is_dir() -> иконка папки, иначе -> ноты
        self.icon.setIcon(FIF.MUSIC_FOLDER if is_dir else FIF.MUSIC) 
        self.icon.setFixedSize(24, 24)
        
        # Текст (имя файла/папки)
        self.label = BodyLabel(self.filename)
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        
        # Добавляем элементы в layout
        self.h_layout.addWidget(self.icon)
        self.h_layout.addWidget(self.label)
        self.h_layout.addStretch(1) # Растягиваем пустое место справа
        
        # Опционально: эффект нажатия
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        print(f"Clicked on: {self.filename}")
        self.itemClicked.emit(self.filename)


class MainFluentWindow(FluentWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MainFluentWindow")

        self.homeInterface = HomeWindow(self)
        setTheme(Theme.DARK)
        

        self.addSubInterface(
            self.homeInterface, 
            icon=FIF.HOME,
            text="Home", 
            position=NavigationItemPosition.TOP
        )
        self.navigationInterface.addItem(
            routeKey='settingInterface',
            icon=FIF.SETTING,
            text='Settings',
            position=NavigationItemPosition.BOTTOM,
        )


class HomeWindow(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeWindow")
        self.file_browser = FileBrowserModel()

        # Main vertical layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)

        # Create scroll area
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True) # resize with content

        # Container for elements in scroll area
        self.view_container = QWidget()
        self.view_layout = VBoxLayout(self.view_container)
        self.view_layout.setContentsMargins(16,16,16,16)
        self.view_layout.setSpacing(8) # Spacing between elements

        # Set container in scroll area
        self.scroll_area.setWidget(self.view_container)
        # Add scroll in main layout
        self.main_layout.addWidget(self.scroll_area)

        self.file_browser.directoryChanged.connect(self._load_dir)

        self.setLayout(self.main_layout)
        self._load_dir()


    def on_back_requested(self):
        self.file_browser.back_previous_dir()


    def _load_dir(self):
        items = self.file_browser.current_dir
        self._render_items(items)
        
        # # Опционально: Управление видимостью кнопки "Назад"
        # # Если мы в корне, кнопку можно сделать неактивной или скрытой
        # main_window = self.window() # Получаем главное окно
        # if hasattr(main_window, 'return_btn'):
        #     if self.file_browser.current_pos == self.file_browser.root_path:
        #         main_window.return_btn.setEnabled(False)
        #         main_window.return_btn.setVisible(False)
        #     else:
        #         main_window.return_btn.setEnabled(True)
        #         main_window.return_btn.setVisible(True)


    def _render_items(self, items: dict[int,Path]):
        # Clear view layout
        while self.view_layout.count():
            item = self.view_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # If not root add back button [..]
        if self.file_browser.current_pos != self.file_browser.root_path:
            prev_path = self.file_browser.current_pos.parent
            prev_item = FileListItem("[..]", True)
            prev_item.clicked.connect(self.file_browser.back_previous_dir)
            self.view_layout.addWidget(prev_item)


        # Render new 
        for key, filename in items.items():
            full_path = self.file_browser.current_pos / filename
            if not full_path.exists():
                continue

            file_item = FileListItem(full_path.name, True) if full_path.is_dir() else FileListItem(full_path.name)
            file_item.itemClicked.connect(self.file_browser.handle_item_click)

            self.view_layout.addWidget(file_item)

        self.view_layout.addStretch(1)
        


if __name__ == "__main__":
    print('__main__: start application')
    try:
        app = QApplication(sys.argv)
        
        font = QFont("Circular", 10)
        app.setFont(font)

        main_app = MainFluentWindow()
        main_app.setStyleSheet("background-color: #000000")
        main_app.setBackgroundColor(QColor("#000000"))
        main_app.show()

    except Exception as e:
        print (f'Error on application start ({e})')
    finally:
        try:
            sys.exit(app.exec_())

        except Exception as e:
            print('Error on closing application ({e})')
        finally:
            print('__main__: close application')