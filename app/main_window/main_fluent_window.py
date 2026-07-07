#main_window/main_fluent_window.py
import os
os.environ['QFLUENT_WIDGETS_PRO_TIPS'] = '0'

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QCloseEvent
from qfluentwidgets import FluentIcon as FIF, FluentWindow, NavigationItemPosition, Theme, setTheme

from .home_window import HomeWindow
from .settings_window import SettingsWindow
from app.core import AudioPlayerController, FileBrowserModel, AppState


class MainFluentWindow(FluentWindow):
    def __init__(self, parent=None):
        """ Init file_browser, set min resolution and init UI
        """
        super().__init__(parent)
        setTheme(Theme.DARK)
        self.__set_min_resolution()
        self.setStyleSheet('''
            border: 0px;
            border-style: solid;
        ''')
        self.__create_core_objects()
        self.__create_windows()
        self.__connect_signals()

        self.__init_ui()

        self._restore_session()


    def __create_core_objects(self):
        self.app_state = AppState()
        self.audio_player = AudioPlayerController([], self.app_state, self)     # TODO: избавться от передачи плейлиста на этом уровне
        self.file_browser = FileBrowserModel(self.audio_player, self.app_state, self)


    def __create_windows(self):
        self.home_window = HomeWindow(self.app_state, self)
        self.settings_window = SettingsWindow(self.app_state, self)


    def __connect_signals(self):
        ''' Connect core logic with UI '''
        self.audio_player.sessionRestored.connect(self.home_window.player_bar._update_info_panel)
        self.audio_player.playbackStateChanged.connect(self.home_window.player_bar._on_playback_state_changed)
        # Signals AudioPlayerController -> PlayerBar
        self.audio_player.shuffleButtonEnabled.connect(self.home_window.player_bar._toggle_shuffle_button)
        self.audio_player.trackChanged.connect(self.home_window.player_bar._update_info_panel)
        self.audio_player.trackSliderChanged.connect(self.home_window.player_bar._update_progress_slider)
        # Signals PlayerBar -> AudioPlayerController
        self.home_window.player_bar.shuffle_button.clicked.connect(self.audio_player.shuffle_playlist)
        self.home_window.player_bar.prev_button.clicked.connect(self.audio_player.prev_track)
        self.home_window.player_bar.togglePlayBtn.connect(self.audio_player.pause_track)
        self.home_window.player_bar.next_button.clicked.connect(self.audio_player.next_track)
        self.home_window.player_bar.audioSliderReleased.connect(self.audio_player.seek)
        self.home_window.player_bar.toggleMuteBtn.connect(self.audio_player.toggle_mute)
        self.home_window.player_bar.volumeSliderChanged.connect(self.audio_player.set_volume)
        # TODO: ADD Repeat button connect

        # Сохранение состояния при смене трека (в память, не в файл!)
        self.audio_player.trackChanged.connect(self._on_track_changed)  # TODO: переделать впервую очередь. вынести из класса

        self.home_window.itemClicked.connect(self.file_browser.handle_item_click)
        self.home_window.backRequested.connect(self.file_browser.back_previous_dir)
        self.home_window.requestDirectory.connect(self.file_browser.load_directory)

        self.file_browser.directoryLoaded.connect(self.home_window.onDirectoryLoaded)
        self.file_browser.directoryChanged.connect(self.home_window.requestDirectory)

        self.home_window.requestDirectory.emit()


    def _restore_session(self):
        """
        Invoke restoring last track.
        If file exist, load it in player and update UI on start of track.
        """
        success = self.audio_player.restore_last_session()


    def _on_track_changed(self, title: str, artist: str, album: str, cover: object):
        """Update state in appstate class when track changed.
        Move this code from mainfluentwindow to appstate
        """
        if self.audio_player.current_playlist:
            current_path = self.audio_player.current_playlist[self.audio_player.current_track_index]
            self.app_state.save_playlist_state(
                self.audio_player.current_playlist,
                self.audio_player.current_track_index,
                current_path
            )


    def closeEvent(self, event: QCloseEvent):
        """
        Override closing window event.
        Save state in file.
        """
        # if self.file_browser:
        #     self.app_state.current_library_path = str(self.file_browser.current_pos)
        
        self.app_state.save()
        super().closeEvent(event)


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
        self.setWindowTitle("Flacify")
        self.__resize_to_center(200,200)
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


    def __resize_to_center(self, width: int = None, height: int = None) -> None:
        """ Make resize to center of screen
        Args:
            width (int, optional): _description_. Defaults to None.
            height (int, optional): _description_. Defaults to None.
        """
        width = max(width, self.__min_width)
        height = max(height, self.__min_height)
        self.resize(width, height)
        self.move(QApplication.primaryScreen().availableGeometry().center() - self.rect().center())