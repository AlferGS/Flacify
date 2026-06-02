# app/PlayerBar.py
from PyQt5.QtWidgets import (
    QSlider,
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel,
    QWidget
)
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtGui import QColor, QPainter
from qfluentwidgets import (
    TransparentToolButton, 
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

class PlayerBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__init_ui()


    def __init_ui(self) -> None:
        print("PlayerBar.py: start __init_ui")
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(10)
        
        
        info_layout = self.__create_info_panel()
        control_layout = self.__create_control_panel()
        vol_layout = self.__create_volume_panel()
        
        # get all together
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(control_layout)
        layout.addStretch()
        layout.addLayout(vol_layout)

        print("PlayerBar.py: end __init_ui")


    def __create_info_panel(self) -> QHBoxLayout:
        """ Set parameters for info panel (albom icon, song name, artist name) """
        print("PlayerBar.py: start __create_info_panel")

        info_layout = QHBoxLayout()
        cover = QLabel()
        cover.setFixedSize(60, 60)
        cover.setStyleSheet("background: #111; border-radius: 4px;")
        
        texts = QVBoxLayout()
        song_title = QLabel("Song Title")
        song_title.setStyleSheet("color: white; font-size: 14px;")
        artist_label = QLabel("Artist")
        artist_label.setStyleSheet("color: #b3b3b3; font-size: 12px;")
        
        texts.addWidget(song_title)
        texts.addWidget(artist_label)
        info_layout.addWidget(cover)
        info_layout.addLayout(texts)
        info_layout.addStretch()

        print("PlayerBar.py: end __create_info_panel")
        return info_layout
    

    def __create_control_panel(self) -> QVBoxLayout:
        """ Set parameters for control panel (next/prev song button, play/stop button, song slider) """
        print("PlayerBar.py: start __create_control_panel")
        control_layout = QVBoxLayout()
        btns = QHBoxLayout()

        # ------------------------------------------------------
        # Add Shuffle queue button
        # ------------------------------------------------------

        prev_button = TransparentToolButton(FIF.CARE_LEFT_SOLID)
        
        play_button = TransparentToolButton(FIF.PLAY)
        play_button.setFixedSize(30, 30)
        play_button.setStyleSheet("""
            TransparentToolButton {
                background-color: #1DB954;
                border-radius: 15px;
            }
            TransparentToolButton:hover {
                background-color: #1ED760;
            }
            TransparentToolButton:pressed {
                background-color: #169c46;
            }
        """)
        
        next_button = TransparentToolButton(FIF.CARE_RIGHT_SOLID)

        # ------------------------------------------------------
        # Add Repeat button
        # ------------------------------------------------------
        
        btns.addStretch()
        btns.addWidget(prev_button)
        btns.addWidget(play_button)
        btns.addWidget(next_button)
        btns.addStretch()

        player_slider = QSlider(Qt.Horizontal)
        player_slider.setStyleSheet("""
            QSlider::groove:horizontal { 
                background: #333; 
                height: 4px; 
                border-radius: 2px; 
            }
            QSlider::sub-page:horizontal { 
                background: #1DB954; 
                border-radius: 2px; 
            }
            QSlider::handle:horizontal { 
                background: #fff; 
                width: 10px; 
                margin: -3px 0; 
                border-radius: 5px; 
            }
        """)
        player_slider.setFixedWidth(450)

        control_layout.addStretch()
        control_layout.addLayout(btns)
        control_layout.addWidget(player_slider)
        control_layout.addStretch()

        print("PlayerBar.py: end __create_control_panel")
        return control_layout


    def __create_volume_panel(self) -> QHBoxLayout:
        """ Set parameters for volume panel (mute button, volume slider) """
        print("PlayerBar.py: start __create_volume_panel")
        vol_layout = QHBoxLayout()
        
        vol_button = TransparentToolButton(FIF.VOLUME)
        
        # Add min size for slider. 
        # Add change style on hover
        vol_slider = QSlider(Qt.Horizontal)
        vol_slider.setStyleSheet("""
            QSlider::groove:horizontal { 
                background: #333; 
                height: 4px; 
                border-radius: 2px; 
            }
            QSlider::sub-page:horizontal { 
                background: #1DB954; 
                border-radius: 2px; 
            }
            QSlider::handle:horizontal { 
                background: #fff; 
                width: 10px; 
                margin: -3px 0; 
                border-radius: 5px; 
            }
        """)
        vol_slider.setFixedWidth(100)
        
        vol_layout.addWidget(vol_button)
        vol_layout.addWidget(vol_slider)

        print("PlayerBar.py: end __create_volume_panel")
        return vol_layout


    def paintEvent(self, event):
        """ Override paintEvent to forced painting black background """
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#000000"))
        painter.end()