#components/file_list_item.py
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QBrush
from qfluentwidgets import BodyLabel, CardWidget, FluentIcon as FIF, IconWidget

class FileListItem(CardWidget):
    """ Class for elements in view layout
    """
    itemClicked = pyqtSignal(str)
    def __init__(self, filename: str, is_dir: bool=False, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.is_dir = is_dir
        self.setFixedHeight(46)
        self.setObjectName("FileListItem")

        # Create main layout
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setSpacing(8)

        # Set icon
        self.icon = IconWidget()
        self.icon.setIcon(FIF.MUSIC_FOLDER if self.is_dir else FIF.MUSIC)
        self.icon.setFixedSize(20,20)

        # Filename label
        self.label = BodyLabel(self.filename)
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.label.setContentsMargins(0, 0, 0, 0)
        self.label.setStyleSheet("color: #FFFFFF; background: transparent;")

        # Add element in layout
        self.h_layout.addWidget(self.icon)
        self.h_layout.addSpacing(5)
        self.h_layout.addWidget(self.label)
        self.h_layout.addStretch(1)

        self.clicked.connect(self._on_clicked)

    
    def _on_clicked(self):
        self.itemClicked.emit(self.filename)


    def paintEvent(self, event):
        """
        Переопределяем отрисовку, чтобы скрыть нативную рамку CardWidget.
        """
        # 1. Сначала даем CardWidget отрисовать себя (включая его рамку)
        super().paintEvent(event)
        
        # 2. Рисуем наш фон ПОВЕРХ рамки, чтобы полностью её перекрыть
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        
        # Выбираем цвет в зависимости от состояния
        if self.isHover or self.isPressed:
            bg_color = QColor("#1F1F1F")
            self.icon.setIcon(FIF.RIGHT_ARROW if self.is_dir else FIF.PLAY)
        else:
            bg_color = QColor("#111111")
            self.icon.setIcon(FIF.MUSIC_FOLDER if self.is_dir else FIF.MUSIC)
            
        # Заливаем фон (рамка CardWidget окажется под этим слоем)
        painter.fillPath(path, QBrush(bg_color))
        
        # Дочерние виджеты (иконка и BodyLabel) отрисуются Qt автоматически 
        # поверх этого фона после завершения paintEvent.