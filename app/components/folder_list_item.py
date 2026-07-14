#components/file_list_item.py
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QBrush
from qfluentwidgets import BodyLabel, CardWidget, FluentIcon as FIF, IconWidget

class FolderListItem(CardWidget):
    """Class for elements in view layout"""
    itemClicked = pyqtSignal(str)
    def __init__(self, folder_name: str, parent=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.setFixedHeight(46)
        self.setObjectName("FolderListItem")

        # Create main layout
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setSpacing(8)

        # Set icon
        self.icon = IconWidget()
        self.icon.setIcon(FIF.MUSIC_FOLDER)
        self.icon.setFixedSize(20,20)

        # Filename label
        self.label = BodyLabel(self.folder_name)
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.label.setContentsMargins(0, 0, 0, 0)
        self.label.setStyleSheet("color: #FFFFFF; background: transparent;")

        # Add elements in layout
        self.h_layout.addWidget(self.icon)
        self.h_layout.addSpacing(5)
        self.h_layout.addWidget(self.label)
        self.h_layout.addStretch(1)

        self.clicked.connect(self.__on_clicked)

    
    def __on_clicked(self):
        self.itemClicked.emit(self.folder_name)


    def paintEvent(self, event):
        """Override the rendering to hide the native CardWidget frame."""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        
        if self.isHover or self.isPressed:
            bg_color = QColor("#1F1F1F")
            self.icon.setIcon(FIF.RIGHT_ARROW)
        else:
            bg_color = QColor("#111111")
            self.icon.setIcon(FIF.MUSIC_FOLDER)
            
        painter.fillPath(path, QBrush(bg_color))