from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QLabel,
    QFrame
)
from PyQt5.QtCore import Qt
from qfluentwidgets import PushButton
from app.PlayerBar import PlayerBar

# Home application page
class HomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.__init_ui()

    def __init_ui(self) -> None:
        self.setObjectName("HomeWindow") 

        main_vert_layout = QVBoxLayout(self)
        main_vert_layout.setContentsMargins(15, 5, 15, 5)
        main_vert_layout.setAlignment(Qt.AlignCenter)
        
        albom_page_layout = QVBoxLayout(self)
        label = QLabel("This is Home Page")
        btn = PushButton("Hello")

        player_bar = PlayerBar()

        albom_page_layout.addWidget(label)
        albom_page_layout.addWidget(btn)
        albom_page_layout.addWidget(label)

        #main_vert_layout.addWidget(label)
        #main_vert_layout.addWidget(btn)
        main_vert_layout.addLayout(albom_page_layout)
        main_vert_layout.addStretch(1)
        main_vert_layout.addWidget(player_bar)