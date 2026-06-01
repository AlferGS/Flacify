from PyQt5.QtWidgets import (
    QSlider,
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel
)
from PyQt5.QtCore import Qt, QObject, QEvent, QSize
from PyQt5.QtGui import QColor
from qfluentwidgets import (
    CardWidget,
    TransparentToolButton, 
    PillToolButton, 
    PushButton,
    FluentIcon as FIF
)

class NoHoverFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.HoverEnter,
                            QEvent.Type.HoverLeave,
                            QEvent.Type.Enter,
                            QEvent.Type.Leave):
            return True
        return super().eventFilter(obj, event)

class PlayerBar(CardWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(80) # Фиксированная высота, как в Spotify
        self.setBackgroundColor(QColor("#000000"))
        self.installEventFilter(NoHoverFilter())
        
        layout = QHBoxLayout(self)
        
        layout.setContentsMargins(15, 5, 15, 5)
        
        # 1. Информация о треке (Слева)
        info_layout = QHBoxLayout()
        cover = QLabel()
        cover.setFixedSize(60, 60)
        cover.setStyleSheet("background: #111; border-radius: 4px;")
        texts = QVBoxLayout()
        
        song_title = QLabel("Song Title")
        song_title.setStyleSheet("color: white;")

        texts.addWidget(QLabel("Song Title"))
        texts.addWidget(QLabel("Artist"))
        info_layout.addWidget(cover)
        info_layout.addLayout(texts)
        
        # 2. Управление (Центр)
        control_layout = QVBoxLayout()
        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(TransparentToolButton(FIF.CARE_LEFT_SOLID))
        
        play_button = PillToolButton(" ")
        play_button.setIcon(FIF.PLAY)
        play_button.setFixedSize(30, 30)
        play_button.setLayoutDirection(Qt.RightToLeft)
        play_button.setStyleSheet("""
            PillToolButton {
                background-color: #1DB954;
                border: none;
                border-radius: 13px;
                padding-left: 1px;
                qproperty-iconSize: 20px 20px;
            }
            PushButton:hover {
                background-color: #1ED760;
            }
            PushButton:pressed {
                background-color: #169c46;
            }
        """)

        # ВАЖНО: Иногда иконка смещается из-за внутреннего выравнивания.
        # Этот хак заставляет иконку рисоваться строго по центру:
        play_button.setLayoutDirection(Qt.LeftToRight) 

        # Вариант Б: Овальная кнопка с текстом
        # play_button.setText("Play")
        # play_button.setFixedHeight(40)
        # play_button.setStyleSheet("""
        #     PushButton {
        #         border-radius: 20px; /* Половина от высоты */
        #         padding: 0 20px;
        #         background-color: #1DB954;
        #         ...
        #     }
        # """)

        btns.addWidget(play_button)

        #btns.addWidget(PillToolButton(FIF.PLAY))
        btns.addWidget(TransparentToolButton(FIF.CARE_RIGHT_SOLID))
        btns.addStretch()
        
        slider = QSlider(Qt.Horizontal)
        slider.setStyleSheet("""
            QSlider::groove:horizontal { background: #333; height: 4px; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #1DB954; border-radius: 2px; }
            QSlider::handle:horizontal { background: #fff; width: 10px; margin: -3px 0; border-radius: 5px; }
        """)
        
        control_layout.addLayout(btns)
        control_layout.addWidget(slider)
        
        # 3. Громкость (Справа)
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(TransparentToolButton(FIF.VOLUME))
        vol_slider = QSlider(Qt.Horizontal)
        vol_slider.setStyleSheet("""
            QSlider::groove:horizontal { background: #333; height: 4px; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #1DB954; border-radius: 2px; }
            QSlider::handle:horizontal { background: #fff; width: 10px; margin: -3px 0; border-radius: 5px; }
        """)
        vol_slider.setFixedWidth(100)
        vol_layout.addWidget(vol_slider)
        
        # Собираем всё вместе
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(control_layout)
        layout.addStretch()
        layout.addLayout(vol_layout)
        
