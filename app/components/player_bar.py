#components/player_bar.py
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout

from qfluentwidgets import FluentIcon as FIF, SimpleCardWidget, TransparentToolButton

from app.core import AppState
from .marquee_label import MarqueeLabel
from .hover_slider import HoverSlider


class PlayerBar(SimpleCardWidget):
    togglePlayBtn = pyqtSignal()            # toggle by click play btn
    toggleMuteBtn = pyqtSignal()            # toggle by click mute btn
    audioSliderReleased = pyqtSignal(int)   # emit audioContr seek
    volumeSliderChanged = pyqtSignal(float) # emit audioContr seek

    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.setObjectName("PlayerBar")
        self.app_state = app_state
        self._is_muted = False
        self._is_slider_pressed = False
        self._total_duration_ms = 0
        
        self.__init_ui()
        
       
    def __init_ui(self) -> None:
        print("PlayerBar.py: start __init_ui")
        self.setFixedHeight(80)
        self.setBorderRadius(16)
        self.setStyleSheet("""
            SimpleCardWidget {
                background-color: #181818;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)

        layout = QGridLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(10)
        
        self.info_layout = self.__create_info_panel()
        self.control_layout = self.__create_control_panel()
        self.vol_layout = self.__create_volume_panel()
        
        layout.addLayout(self.info_layout,0,0)
        layout.addLayout(self.control_layout,0,1)
        layout.addLayout(self.vol_layout,0,2)

        self.layout = layout


    @staticmethod
    def __format_time(ms: int) -> str:
        if ms < 0: ms = 0
        seconds = ms // 1000
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"


    def __create_info_panel(self) -> QHBoxLayout:
        """ Set parameters for info panel (album icon, song name, artist name) 
        """
        info_layout = QHBoxLayout()

        # Cover lable
        self.cover = QLabel()
        self.cover.setFixedSize(60, 60)
        self.cover.setAlignment(Qt.AlignCenter)
        self.cover.setText("No Cover")
        self.cover.setStyleSheet("color: #555; background: #111; border-radius: 4px")
        
        texts = QVBoxLayout()
        self.song_title = MarqueeLabel("No track selected")
        self.song_title.setStyleSheet("color: white; font-size: 14px;")
        self.song_title.setFixedWidth(125)
        self.artist_label = MarqueeLabel("Unknown Artist")
        self.artist_label.setStyleSheet("color: #b3b3b3; font-size: 12px;")
        self.artist_label.setFixedWidth(125)
        
        texts.addWidget(self.song_title)
        texts.addWidget(self.artist_label)
        info_layout.addWidget(self.cover)
        info_layout.addLayout(texts)
        info_layout.setAlignment(Qt.AlignLeft)
        return info_layout
    

    def _update_info_panel(self, title:str, artist:str, album: str, cover_data: object) -> None:
        self.song_title.setText(title)
        self.artist_label.setText(f"{artist}")

        if cover_data:
            pixelmap = QPixmap()
            if pixelmap.loadFromData(cover_data) and not pixelmap.isNull():
                scaled_pixmap = pixelmap.scaled(
                    self.cover.size(), 
                    Qt.KeepAspectRatioByExpanding, 
                    Qt.SmoothTransformation
                )
                self.cover.setPixmap(scaled_pixmap)
                self.cover.setText("")
            else:
                self._set_default_cover()
        else:
            self._set_default_cover()


    def _set_default_cover(self):
        self.cover.clear()
        self.cover.setText("No Cover")
        self.cover.setStyleSheet("color: #555; background: #111; border-radius: 4px;")


    def __create_control_panel(self) -> QVBoxLayout:
        """ Set parameters for control panel (next/prev song button, play/stop button, song slider) """
        control_layout = QVBoxLayout()
        btns_layout = QHBoxLayout()

        self.shuffle_button = TransparentToolButton(FIF.SYNC)
        self.shuffle_button.setFixedSize(30, 30)
        # self.shuffle_button.setEnabled(False)

        self.prev_button = TransparentToolButton(FIF.CARE_LEFT_SOLID)
        self.prev_button.setFixedSize(30, 30)
        self.play_button = TransparentToolButton(FIF.PLAY)
        self.play_button.setFixedSize(30, 30)
        self.play_button.setStyleSheet("""
            TransparentToolButton {
                background-color: #1DB954;
                border-radius: 15px;
            }
            TransparentToolButton:hover {
                background-color: #1DB954;
            }
            TransparentToolButton:pressed {
                background-color: #169c46;
            }
        """)
        self.play_button.clicked.connect(self._on_play_clicked)
        self.next_button = TransparentToolButton(FIF.CARE_RIGHT_SOLID)
        self.next_button.setFixedSize(30, 30)
        self.repeat_button = TransparentToolButton(FIF.ROTATE)
        self.repeat_button.setFixedSize(30, 30)
        
        btns_layout.addStretch()
        btns_layout.addWidget(self.shuffle_button)
        btns_layout.addWidget(self.prev_button)
        btns_layout.addWidget(self.play_button)
        btns_layout.addWidget(self.next_button)
        btns_layout.addWidget(self.repeat_button)
        btns_layout.addStretch()
        btns_layout.setAlignment(Qt.AlignCenter)

        slider_layout = QHBoxLayout()
        self.current_track_time = QLabel("00:00")
        self.current_track_time.setStyleSheet("color: #b3b3b3; font-size: 11px; min-width: 40px;")
        self.current_track_time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.player_slider = HoverSlider(Qt.Horizontal)
        self.player_slider.setRange(0, 1000) 
        self.player_slider.setValue(0)
        self.player_slider.setMinimumWidth(350)
        self.player_slider.setMaximumWidth(500)
        self.player_slider.sliderPressed.connect(self.__on_slider_pressed)
        self.player_slider.sliderReleased.connect(self.__on_slider_released)
        self.player_slider.valueChanged.connect(self.__on_slider_value_changed)

        self.song_duration = QLabel("00:00")
        self.song_duration.setStyleSheet("color: #b3b3b3; font-size: 11px; min-width: 40px;")
        self.song_duration.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        slider_layout.addWidget(self.current_track_time)
        slider_layout.addWidget(self.player_slider)
        slider_layout.addWidget(self.song_duration)
        slider_layout.setAlignment(Qt.AlignCenter)

        control_layout.addSpacing(7)
        control_layout.addLayout(btns_layout)
        control_layout.addLayout(slider_layout)
        control_layout.setAlignment(Qt.AlignCenter)
        return control_layout


    def __on_slider_value_changed(self, value: int):
        """
        Update value for self.current_track_time
        """
        time_str = self.__format_time(value)
        self.current_track_time.setText(time_str)


    def __on_slider_pressed(self):
        self._is_slider_pressed = True


    def __on_slider_released(self):
        self._is_slider_pressed = False

        if self._total_duration_ms > 0:
            position_ms = self.player_slider.value()
            self.current_track_time.setText(self.__format_time(position_ms))
            self.audioSliderReleased.emit(position_ms)


    def __create_volume_panel(self) -> QHBoxLayout:
        """ Set parameters for volume panel (mute button, volume slider) """
        vol_layout = QHBoxLayout()
        
        self.vol_button = TransparentToolButton(FIF.VOLUME)
        self.vol_button.clicked.connect(self.__vol_button_clicked)
        
        # TODO: Add min size for slider. 
        # TODO: Add change style on hover
        self.vol_slider = HoverSlider(Qt.Horizontal)
        self.vol_slider.setMinimumWidth(65)
        self.vol_slider.setMaximumWidth(85)
        self.vol_slider.setValue(int(self.app_state.volume*100))
        self.vol_slider.valueChanged.connect(self.__on_volume_changed)
        
        vol_layout.addWidget(self.vol_button)
        vol_layout.addWidget(self.vol_slider)
        vol_layout.setAlignment(Qt.AlignRight)
        return vol_layout


    def __vol_button_clicked(self):
        self._is_muted = not self._is_muted
        self.__sync_volume_ui(self._is_muted)
        self.toggleMuteBtn.emit()


    def __sync_volume_ui(self, is_muted: bool):
        """Used when vol_button clicked."""
        self.vol_slider.blockSignals(True)
        try:
            if is_muted:
                self.vol_button.setIcon(FIF.MUTE)
                self.vol_slider.setValue(0)
            else:
                self.vol_button.setIcon(FIF.VOLUME)
                self.vol_slider.setValue(int(self.app_state.volume * 100))
        finally:
            self.vol_slider.blockSignals(False)


    def _update_progress_slider(self, current_ms: int, total_ms: int):
        self._total_duration_ms = total_ms
        self.song_duration.setText(self.__format_time(total_ms))
        
        if self._is_slider_pressed:
            return
        
        self.current_track_time.setText(self.__format_time(current_ms))
        
        self.player_slider.blockSignals(True)
        try:
            if total_ms > 0:
                self.player_slider.setRange(0, total_ms)
                self.player_slider.setValue(current_ms)
        finally:
            self.player_slider.blockSignals(False)


    def __on_volume_changed(self, volume: int):
        """Called when vol_slider moved."""
        vol_float = float(volume / 100.0)
        self.volumeSliderChanged.emit(vol_float)
        
        if volume == 0:
            self.vol_button.setIcon(FIF.MUTE)
        else:
            self.vol_button.setIcon(FIF.VOLUME)


    def _toggle_shuffle_button(self, flag: bool) -> None:
        self.shuffle_button.setEnabled(flag)


    def _on_playback_state_changed(self, is_playing: bool):
        """
        Слот, вызываемый контроллером при изменении состояния Play/Pause.
        Обновляет иконку кнопки.
        """
        if is_playing:
            self.play_button.setIcon(FIF.PAUSE)
        else:
            self.play_button.setIcon(FIF.PLAY)


    def _on_play_clicked(self):
        self.togglePlayBtn.emit()


    def paintEvent(self, event):
        """ Override paintEvent to forced painting black background """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#000000"))
        painter.end()