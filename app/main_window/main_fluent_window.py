#main_window/main_fluent_window.py
import os

os.environ['QFLUENT_WIDGETS_PRO_TIPS'] = '0'

from PyQt5.QtWidgets import QApplication

from qfluentwidgets import FluentIcon as FIF, FluentWindow, NavigationItemPosition, Theme, setTheme

from .home_window import HomeWindow
from .settings_window import SettingsWindow
from app.core import AudioPlayerController, FileBrowserModel


class MainFluentWindow(FluentWindow):
    def __init__(self, parent=None):
        """ Init file_browser, set min resolution and init ui
        """
        super().__init__(parent)
        setTheme(Theme.DARK)
        self.__set_min_resolution()
        self.setStyleSheet('''
            border: 0px;
            border-style: solid;
        ''')
        self.audio_player = AudioPlayerController([], self)
        self.file_browser = FileBrowserModel(self.audio_player, self)
        self.home_window = HomeWindow(self.file_browser, self.audio_player, self)
        self.settings_window = SettingsWindow(self)

        self.audio_player.shuffleButtonEnabled.connect(self.home_window.player_bar._toggle_shuffle_button)
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

        #---------------------------------------
        # TODO: Add scroll albums
        #---------------------------------------

        self.addSubInterface(
            self.home_window, 
            icon=FIF.HOME,
            text="Home", 
            position=NavigationItemPosition.TOP
        )

        #---------------------------------------
        # TODO: Add albums with NavigationItemPosition.SCROLL
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