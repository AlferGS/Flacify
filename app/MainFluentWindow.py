import os
os.environ['QFLUENT_WIDGETS_PRO_TIPS'] = '0'
from qfluentwidgets import (
    FluentWindow, 
    NavigationItemPosition,
    NavigationInterface,
    setTheme, 
    Theme,
    FluentIcon as FIF
)
from PyQt5.QtWidgets import QApplication, QPushButton, QLabel, QWidget, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette

from app.HomeWindow import HomeWindow
from app.SettingsWindow import SettinsWindow
from app.FileBrowserModel import FileBrowserModel
from app.AudioPlayerController import AudioPlayerController

# Main appliction class
class MainFluentWindow(FluentWindow):
    def __init__(self, parent=None):
        """ Init filebrowser, set min resolution and init ui
        """
        super().__init__(parent)
        self.file_browser = FileBrowserModel(self)

        setTheme(Theme.DARK)
        self.__set_min_resolution()
        self.__init_ui()

    def __set_min_resolution(self) -> None:
        """ Set min resolution for window
        1/4 of primary window
        """
        screen = QApplication.primaryScreen().geometry()
        self.__min_width = screen.width()//2
        self.__min_height = screen.height()//2
        self.setMinimumSize(self.__min_width, self.__min_height)


    def __init_ui(self) -> None:
        """ Set Window title. Set window in screen center. 
        Create navigation field
        """
        self.setWindowTitle("Spotify Style")
        self.__center(200,200)
        self.__create_nav_field()
        

    def __create_nav_field(self) -> None:
        """ Init windows for navigation bar and add
        it with icons
        """
        # Create Navigation Bar
        self.homeInterface = HomeWindow(self)
        #---------------------------------------
        # Add scroll albums
        #---------------------------------------
        self.settings_window = SettinsWindow(self)

        self.addSubInterface(
            self.homeInterface, 
            icon=FIF.HOME,
            text="Home", 
            position=NavigationItemPosition.TOP
        )

        #---------------------------------------
        # Add albums with NavigationItemPosition.SCROLL
        #---------------------------------------

        self.addSubInterface(
            self.settings_window, 
            icon=FIF.SETTING,
            text="Settings", 
            position=NavigationItemPosition.BOTTOM
        )


    def __center(self, width: int = None, height: int = None) -> None:
        """ Make resize to center of screen
        Args:
            width (int, optional): _description_. Defaults to None.
            height (int, optional): _description_. Defaults to None.
        """
        width = max(width, self.__min_width)
        height = max(height, self.__min_height)
        self.resize(width, height)
        self.move(QApplication.primaryScreen().availableGeometry().center() - self.rect().center())