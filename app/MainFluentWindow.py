from qfluentwidgets import (
    FluentWindow, 
    NavigationItemPosition,
    setTheme, 
    Theme,
    FluentIcon as FIF
)
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor
from app.HomeWindow import HomeWindow
from app.SettingsWindow import SettinsWindow

# Main appliction class
class MainFluentWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.__set_min_resolution()
        self.__initUI()

    def __set_min_resolution(self) -> None:
        screen = QApplication.primaryScreen().geometry()
        self.__min_width = screen.width()//2
        self.__min_height = screen.height()//2
        self.setMinimumSize(self.__min_width, self.__min_height)

    def __initUI(self) -> None:
        setTheme(Theme.DARK)
        self.setBackgroundColor(QColor("#000000"))
        
        self.setWindowTitle("Spotify Style")
        self.__create_nav_field()
        self.__center(200,200)

    def __create_nav_field(self) -> None:

        # Create Navigation Bar
        self.homeInterface = HomeWindow()
        #---------------------------------------
        # Add scroll alboms
        #---------------------------------------
        self.settings_window = SettinsWindow()

        pos = NavigationItemPosition.SCROLL
        self.addSubInterface(
            self.homeInterface, 
            icon=FIF.HOME,
            text="Home", 
            position=NavigationItemPosition.TOP
        )

        #---------------------------------------
        # Add alboms with NavigationItemPosition.SCROLL
        #---------------------------------------

        self.addSubInterface(
            self.settings_window, 
            icon=FIF.SETTING,
            text="Settings", 
            position=NavigationItemPosition.BOTTOM
        )

    def __center(self, width: int = None, height: int = None) -> None:
        width = max(width, self.__min_width)
        height = max(height, self.__min_height)
        self.resize(width, height)
        self.move(QApplication.primaryScreen().availableGeometry().center() - self.rect().center())