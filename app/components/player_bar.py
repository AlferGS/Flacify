# app/PlayerBar.py
from PyQt5.QtWidgets import (
    QApplication,
    QSlider,
    QHBoxLayout, 
    QVBoxLayout, 
    QGridLayout,
    QLabel, QStyleOption, QStyle,
    QWidget, 
    
)
from PyQt5.QtCore import Qt, QObject, QEvent, QTimer, QPoint
from PyQt5.QtGui import QColor, QPainter, QFontMetrics, QPalette, QPixmap, QCursor
from qfluentwidgets import (
    TransparentToolButton, SimpleCardWidget,
    FluentIcon as FIF
)
from app.core import AudioPlayerController

class NoHoverFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.HoverEnter,
                            QEvent.Type.HoverLeave,
                            QEvent.Type.Enter,
                            QEvent.Type.Leave):
            return True
        return super().eventFilter(obj, event)


class MarqueeLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._offset = 0.0
        self._direction = -1  # -1 = едет влево, 1 = вправо
        self._pause_counter = 0
        self._pause_duration = 40  # Тиков паузы (~1.2 сек при 30мс)
        self._step = 1.0  # Пикселей за тик
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_offset)
        self._timer.setInterval(30)
        
    def setText(self, text):
        super().setText(text)
        self._check_animation_needed()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._check_animation_needed()
        
    def _check_animation_needed(self):
        if not self.text():
            self._timer.stop()
            self._offset = 0
            return
            
        metrics = QFontMetrics(self.font())
        # horizontalAdvance доступен в Qt 5.11+, для старых версий width()
        text_width = metrics.horizontalAdvance(self.text()) if hasattr(metrics, 'horizontalAdvance') else metrics.width(self.text())
            
        if text_width > self.width():
            if not self._timer.isActive():
                self._offset = 0.0
                self._direction = -1
                self._pause_counter = self._pause_duration # Пауза перед стартом
                self._timer.start()
        else:
            self._timer.stop()
            self._offset = 0.0
            self.update()
            
    def _update_offset(self):
        metrics = QFontMetrics(self.font())
        text_width = metrics.horizontalAdvance(self.text()) if hasattr(metrics, 'horizontalAdvance') else metrics.width(self.text())
        max_offset = text_width - self.width()
        
        if max_offset <= 0:
            self._timer.stop()
            self._offset = 0.0
            self.update()
            return
            
        if self._pause_counter > 0:
            self._pause_counter -= 1
            return
            
        self._offset += self._direction * self._step
        
        # Логика Ping-Pong с паузами
        if self._direction == -1 and self._offset <= -max_offset:
            self._offset = -max_offset
            self._direction = 1
            self._pause_counter = self._pause_duration
        elif self._direction == 1 and self._offset >= 0:
            self._offset = 0.0
            self._direction = -1
            self._pause_counter = self._pause_duration
            
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        opt = QStyleOption()
        opt.initFrom(self)
        opt.text = self.text()
        
        # Вычисляем ширину текста для расширения области отрисовки
        text_width = self.fontMetrics().horizontalAdvance(self.text()) if hasattr(self.fontMetrics(), 'horizontalAdvance') else self.fontMetrics().width(self.text())
        
        # Создаем rect со смещением
        opt.rect = self.rect().translated(int(self._offset), 0)
        opt.rect.setWidth(max(self.width(), text_width) + 50)
        
        opt.displayAlignment = self.alignment() | Qt.AlignVCenter
        
        # Используем style() для сохранения CSS стилей (цвета, шрифты)
        self.style().drawItemText(
            painter, 
            opt.rect, 
            int(opt.displayAlignment), 
            opt.palette, 
            self.isEnabled(), 
            opt.text, 
            QPalette.WindowText
        )


class HoverSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        
        # Стили
        self.style_default = """
            QSlider::groove:horizontal { 
                background: #333; 
                height: 4px; 
                border-radius: 2px; 
            }
            QSlider::sub-page:horizontal { 
                background: #fff; 
                border-radius: 2px; 
            }
            QSlider::handle:horizontal { 
                background: transparent; /* hide by default */
                width: 10px; 
                height: 10px;
                margin: -3px 0; 
                border-radius: 5px; 
            }
        """
        
        self.style_hover = """
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
                height: 10px;
                margin: -3px 0; 
                border-radius: 5px; 
            }
        """
        
        self.setStyleSheet(self.style_default)
        

    def enterEvent(self, event):
        self.setStyleSheet(self.style_hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.style_default)
        super().leaveEvent(event)


class PlayerBar(SimpleCardWidget):
    def __init__(self, audio_player: AudioPlayerController, parent=None):
        super().__init__(parent)
        self.setObjectName("PlayerBar")
        self.audio_player = audio_player
        self._is_slider_pressed = False
        self._total_duration_ms = 0
        self.__init_ui()
        self.__connect_signals()

       
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
        # layout.addStretch()
        layout.addLayout(self.control_layout,0,1)
        # layout.addStretch()
        layout.addLayout(self.vol_layout,0,2)

        self.layout = layout


    @staticmethod
    def _format_time(ms: int) -> str:
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
    

    def __update_info_panel(self, title:str, artist:str, album: str, cover_data: object) -> None:
        self.song_title.setText(title)
        self.artist_label.setText(f"{artist}")
        self.play_button.setIcon(FIF.PAUSE)

        if cover_data:
            pixelmap = QPixmap()
            pixelmap.loadFromData(cover_data)
            # Масштабируем обложку под размер label, сохраняя пропорции
            scaled_pixmap = pixelmap.scaled(
                self.cover.size(), 
                Qt.KeepAspectRatioByExpanding, 
                Qt.SmoothTransformation
            )
            self.cover.setPixmap(scaled_pixmap)
            self.cover.setText("") # Убираем текст-заглушку
        else:
            self.cover.clear()
            self.cover.setText("No Cover")
            self.cover.setStyleSheet("color: #555; background: #111; border-radius: 4px;")


    def __create_control_panel(self) -> QVBoxLayout:
        """ Set parameters for control panel (next/prev song button, play/stop button, song slider) """
        control_layout = QVBoxLayout()
        btns_layout = QHBoxLayout()

        self.shuffle_button = TransparentToolButton(FIF.SYNC)
        self.shuffle_button.setFixedSize(30, 30)
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
        self.player_slider.sliderPressed.connect(self._on_slider_pressed)
        self.player_slider.sliderReleased.connect(self._on_slider_released)
        self.player_slider.valueChanged.connect(self._on_slider_value_changed)

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


    def _on_slider_value_changed(self, value: int):
        """
        Update value for self.current_track_time
        """
        time_str = self._format_time(value)
        self.current_track_time.setText(time_str)


    def _on_slider_pressed(self):
        self._is_slider_pressed = True


    def _on_slider_released(self):
        self._is_slider_pressed = False

        if self._total_duration_ms > 0:
            position_ms = self.player_slider.value()
            self.audio_player.seek(position_ms)
            self.current_track_time.setText(self._format_time(position_ms))


    def __create_volume_panel(self) -> QHBoxLayout:
        """ Set parameters for volume panel (mute button, volume slider) """
        vol_layout = QHBoxLayout()
        
        self.vol_button = TransparentToolButton(FIF.VOLUME)
        self.vol_button.clicked.connect(self.__vol_button_clicked)
        
        # Add min size for slider. 
        # Add change style on hover
        self.vol_slider = HoverSlider(Qt.Horizontal)
        self.vol_slider.setMinimumWidth(65)
        self.vol_slider.setMaximumWidth(85)
        self.vol_slider.setValue(int(self.audio_player._current_volume*100))        # make get from data class
        self.vol_slider.valueChanged.connect(self.__on_volume_changed)
        
        vol_layout.addWidget(self.vol_button)
        vol_layout.addWidget(self.vol_slider)
        vol_layout.setAlignment(Qt.AlignRight)
        return vol_layout


    def __vol_button_clicked(self):
        is_now_muted = self.audio_player.toggle_mute()
        self.__sync_volume_ui(is_now_muted)


    def __sync_volume_ui(self, is_muted: bool):
        """Used when vol_button clicked."""
        self.vol_slider.blockSignals(True)
        try:
            if is_muted:
                self.vol_button.setIcon(FIF.MUTE)
                self.vol_slider.setValue(0)
            else:
                self.vol_button.setIcon(FIF.VOLUME)
                self.vol_slider.setValue(int(self.audio_player._current_volume * 100))
        finally:
            self.vol_slider.blockSignals(False)


    def _update_progress_slider(self, current_ms: int, total_ms: int):
        self._total_duration_ms = total_ms
        self.song_duration.setText(self._format_time(total_ms))
        
        if self._is_slider_pressed:
            return
        
        self.current_track_time.setText(self._format_time(current_ms))
        
        self.player_slider.blockSignals(True)
        try:
            if total_ms > 0:
                self.player_slider.setRange(0, total_ms)
                self.player_slider.setValue(current_ms)
        finally:
            self.player_slider.blockSignals(False)


    def __connect_signals(self):
        self.shuffle_button.clicked.connect(self.audio_player.shuffle_playlist)
        self.prev_button.clicked.connect(self.audio_player.prev_track)
        self.next_button.clicked.connect(self.audio_player.next_track)
        self.play_button.clicked.connect(self.pause_track)
        self.audio_player.trackChanged.connect(self.__update_info_panel)
        self.audio_player.trackSliderChanged.connect(self._update_progress_slider)


    def __on_volume_changed(self, volume: int):
        """Called when vol_slider moved."""
        vol_float = float(volume / 100.0)
        self.audio_player.set_volume(vol_float)
        
        if volume == 0:
            self.vol_button.setIcon(FIF.MUTE)
        else:
            self.vol_button.setIcon(FIF.VOLUME)


    def pause_track(self):
        self.audio_player.pause_track()
        icon = FIF.PLAY if self.audio_player.is_paused else FIF.PAUSE
        self.play_button.setIcon(icon)


    def paintEvent(self, event):
        """ Override paintEvent to forced painting black background """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # Сглаживание
        painter.fillRect(self.rect(), QColor("#000000"))
        painter.end()