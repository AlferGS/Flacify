from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontMetrics, QPainter, QPalette
from PyQt5.QtWidgets import QStyleOption

from qfluentwidgets import BodyLabel

class MarqueeLabel(BodyLabel):
    def __init__(self, text="", parent=None):
        """Initializes the label, configures scrolling parameters, 
        and sets up the QTimer to drive the animation loop."""

        super().__init__(text)
        self._offset = 0.0
        self._direction = -1        # -1 = goes left, 1 = goes right
        self._pause_counter = 0
        self._pause_duration = 40   # Pause ticks (~1.2 sec at 30 ms)
        self._step = 1.0            # Pixels per tick
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.__update_offset)
        self._timer.setInterval(30)
       

    def __check_animation_needed(self):
        """Compares text width to label width and starts or stops
        the scrolling animation timer accordingly."""

        if not self.text():
            self._timer.stop()
            self._offset = 0
            return
            
        metrics = QFontMetrics(self.font())
        text_width = metrics.horizontalAdvance(self.text()) if hasattr(metrics, 'horizontalAdvance') else metrics.width(self.text())
            
        if text_width > self.width():
            if not self._timer.isActive():
                self._offset = 0.0
                self._direction = -1
                self._pause_counter = self._pause_duration # Pause before the start
                self._timer.start()
        else:
            self._timer.stop()
            self._offset = 0.0
            self.update()


    def __update_offset(self):
        """Updates the horizontal offset, handles direction reversal 
        and pauses at boundaries, and triggers a repaint."""

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
        
        if self._direction == -1 and self._offset <= -max_offset:
            self._offset = -max_offset
            self._direction = 1
            self._pause_counter = self._pause_duration
        elif self._direction == 1 and self._offset >= 0:
            self._offset = 0.0
            self._direction = -1
            self._pause_counter = self._pause_duration
            
        self.update()
         

    def _setText(self, text):
        """Updates the displayed text and re-evaluates whether the marquee animation should be active."""

        super().setText(text)
        self.__check_animation_needed()
        

    def resizeEvent(self, event):
        """Handles widget resizing and re-checks animation requirements based on the new dimensions."""

        super().resizeEvent(event)
        self.__check_animation_needed()
        

    def paintEvent(self, event):
        """Handles widget resizing and re-checks animation requirements based on the new dimensions."""

        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        opt = QStyleOption()
        opt.initFrom(self)
        opt.text = self.text()
        
        text_width = self.fontMetrics().horizontalAdvance(self.text()) if hasattr(self.fontMetrics(), 'horizontalAdvance') else self.fontMetrics().width(self.text())
        
        opt.rect = self.rect().translated(int(self._offset), 0)
        opt.rect.setWidth(max(self.width(), text_width) + 50)
        
        opt.displayAlignment = self.alignment() | Qt.AlignVCenter
        
        self.style().drawItemText(
            painter, 
            opt.rect, 
            int(opt.displayAlignment), 
            opt.palette, 
            self.isEnabled(), 
            opt.text, 
            QPalette.WindowText
        )
