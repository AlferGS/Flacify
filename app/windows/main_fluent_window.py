#windows/main_fluent_window.py
import os
os.environ['QFLUENT_WIDGETS_PRO_TIPS'] = '0'

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QCloseEvent
from qfluentwidgets import FluentIcon as FIF, FluentWindow, NavigationItemPosition, Theme, setTheme

from .home_window import HomeWindow
from .settings_window import SettingsWindow
from app.core import AudioPlayerController, FileBrowserModel, AppState


class MainFluentWindow(FluentWindow):
    """Main window"""
    def __init__(self, parent=None):
        """ Init event.
        Set theme, font, start resolution and position for application.
        Create windows in application and all core objects.
        Try to restore last session.
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

        if not self.__restore_session():
            print("session wasn't restored")


    def __set_min_resolution(self) -> None:
        """ Set min resolution for window
        1/4 of primary window.
        """
        screen = QApplication.primaryScreen().geometry()
        self.__min_width = screen.width()//2
        self.__min_height = screen.height()//2
        self.setMinimumSize(self.__min_width, self.__min_height)


    def __create_core_objects(self):
        """Create objects of classes /core."""
        self.app_state = AppState()
        self.audio_player = AudioPlayerController(self.app_state, self)
        self.file_browser = FileBrowserModel(self.app_state, self)


    def __create_windows(self):
        """Create objects of classes /windows."""
        self.home_window = HomeWindow(self.app_state, self)
        self.settings_window = SettingsWindow(self.app_state, self)


    def __connect_signals(self):
        """Connect core logic with UI."""
        # Signals AudioPlayerController -> PlayerBar
        self.audio_player.sessionRestored.connect(self.home_window.player_bar._update_info_panel)
        self.audio_player.playbackStateChanged.connect(self.home_window.player_bar._on_playback_state_changed)
        self.audio_player.shuffleButtonEnabled.connect(self.home_window.player_bar._toggle_shuffle_button)
        self.audio_player.trackChanged.connect(self.home_window.player_bar._update_info_panel)
        self.audio_player.trackChanged.connect(self.home_window.queue_window._on_track_changed)
        self.audio_player.trackSliderChanged.connect(self.home_window.player_bar._update_progress_slider)
        self.audio_player.repeatModeChanged.connect(self.home_window.player_bar._on_repeat_mode_changed)
        # Signals AudioPlayerController -> QueueWindow
        self.audio_player.trackChanged.connect(self.home_window.queue_window._on_track_changed)
        self.audio_player.updateShuffledPlaylist.connect(self.home_window.queue_window._update_queue)
        # Signals PlayerBar -> AudioPlayerController
        self.home_window.player_bar.shuffle_button.clicked.connect(self.audio_player._shuffle_playlist)
        self.home_window.player_bar.prev_button.clicked.connect(self.audio_player._prev_track)
        self.home_window.player_bar.togglePlayBtn.connect(self.audio_player._pause_track)
        self.home_window.player_bar.next_button.clicked.connect(self.audio_player._next_track)
        self.home_window.player_bar.repeat_button.clicked.connect(self.audio_player._toggle_repeat)
        self.home_window.player_bar.audioSliderReleased.connect(self.audio_player._seek)
        self.home_window.player_bar.toggleMuteBtn.connect(self.audio_player._toggle_mute)
        self.home_window.player_bar.volumeSliderChanged.connect(self.audio_player._set_volume)
        # Signals HomeWindow -> FileBrowserModel
        self.home_window.itemClicked.connect(self.file_browser._handle_item_click)
        self.home_window.backRequested.connect(self.file_browser._back_previous_dir)
        self.home_window.requestDirectory.connect(self.file_browser._load_directory)
        # Signals QueueWindow -> AudioPlayerController
        self.home_window.queue_window.queue_reordered.connect(self.audio_player._update_queue_order)
        self.home_window.queue_window.play_track_requested.connect(self.audio_player._play_file)
        # Signals FileBrowserModel -> HomeWindow
        self.file_browser.directoryLoaded.connect(self.home_window._onDirectoryLoaded)
        self.file_browser.directoryChanged.connect(self.home_window.requestDirectory)
        # Signals FileBrowserModel -> AudioPlayerController
        self.file_browser.playbackStarted.connect(self.audio_player._play_current_track)
        self.file_browser.nextTrack.connect(self.audio_player._next_track)
        self.file_browser.prevTrack.connect(self.audio_player._prev_track)

        self.home_window.requestDirectory.emit()


    def __init_ui(self) -> None:
        """ Set Window title. Set window in screen center. 
        Create navigation field.
        """
        self.setWindowTitle("Flacify")
        self.__resize_to_center(200,200)
        self.__create_nav_field()
        

    def __restore_session(self):
        """
        Invoke restoring last track.
        If file exist, load it in player and update UI on start of track.
        """
        return self.audio_player._restore_last_session()


    def __create_nav_field(self) -> None:
        """ Init windows for navigation bar and add
        it with icons.
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
        """ Make resize to center of screen.
        Args:
            width (int, optional): _description_. Defaults to None.
            height (int, optional): _description_. Defaults to None.
        """
        width = max(width, self.__min_width)
        height = max(height, self.__min_height)
        self.resize(width, height)
        self.move(QApplication.primaryScreen().availableGeometry().center() - self.rect().center())


    def closeEvent(self, event: QCloseEvent):
        """
        Override closing window event.
        Save state in file.
        """
        self.app_state._save()
        super().closeEvent(event)
