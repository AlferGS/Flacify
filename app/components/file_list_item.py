from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout

from qfluentwidgets import BodyLabel, CardWidget, FluentIcon as FIF, IconWidget

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
