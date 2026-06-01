from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QLabel
)
from PyQt5.QtCore import Qt
from qfluentwidgets import CheckBox

# 2. Страница Настроек
class SettinsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.__initUI()


    def __initUI(self):
        self.setObjectName("Settings Window")

        self.vbox = QVBoxLayout(self)
        self.vbox.setAlignment(Qt.AlignCenter)

        main_label = QLabel("<b>Settings<\b>")
        checkbox = CheckBox("Settings cb", self)
        
        self.vbox.addWidget(main_label)
        self.vbox.addWidget(checkbox)
