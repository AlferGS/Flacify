from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QLabel
)
from PyQt5.QtCore import Qt
from qfluentwidgets import PushButton
from app.PlayerBar import PlayerBar

# 1. Создаем страницу (Интерфейс)
class HomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setObjectName("HomeWindow") 

        v_layout = QVBoxLayout(self)
        v_layout.setAlignment(Qt.AlignCenter)
        
        label = QLabel("This is Home Page")
        btn = PushButton("Hello")
        player_bar = PlayerBar()

        v_layout.addWidget(label)
        v_layout.addWidget(btn)
        v_layout.addStretch(1)
        v_layout.addWidget(player_bar)
