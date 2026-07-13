from PyQt5.QtWidgets import QSlider

class HoverSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        
        # Styles
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
