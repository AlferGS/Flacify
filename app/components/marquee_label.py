from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontMetrics, QPainter, QPalette
from PyQt5.QtWidgets import QLabel, QStyleOption

from qfluentwidgets import BodyLabel

class MarqueeLabel(BodyLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text)
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

