#windows/main_fluent_window.py
import os
from pathlib import Path
os.environ['QFLUENT_WIDGETS_PRO_TIPS'] = '0'

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QCloseEvent, QIcon
from qfluentwidgets import FluentIcon as FIF, FluentWindow, NavigationItemPosition, Theme, setTheme

from .home_window import HomeWindow
from .settings_window import SettingsWindow
from app.core import AudioPlayerController, FileBrowserModel, AppState

from app.core.playlist_manager import PlaylistManager
# from app.core.playlist import Playlist
# from app.windows.playlists_window import PlaylistsWindow
from app.windows.playlist_detail_window import PlaylistDetailWindow
# from app.components.playlist_badge import PlaylistBadge
from app.components.create_playlist_dialog import CreatePlaylistDialog
from app.components.add_to_playlist_dialog import AddToPlaylistDialog


class MainFluentWindow(FluentWindow):
    """Main window"""
    def __init__(self, parent=None):
        """ Init event.
        Set theme, font, start resolution and position for application.
        Create windows in application and all core objects.
        Try to restore last session.
        """
        super().__init__(parent)
        
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
        icon_path = os.path.abspath(icon_path)
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"[Warning] Icon not found: {icon_path}")
            
        setTheme(Theme.DARK)
        self.__set_min_resolution()
        self.setStyleSheet('''
            border: 0px;
            border-style: solid;
        ''')
        self.__create_core_objects()
        self.__create_playlist_manager_core()
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


    def __create_core_objects(self) -> None:
        """Create objects of classes /core."""
        self.app_state = AppState()
        self.audio_player = AudioPlayerController(self.app_state, self)
        self.file_browser = FileBrowserModel(self.app_state, self)


    def __create_playlist_manager_core(self) -> None:
        # playlists manager
        self.playlist_manager = PlaylistManager(
            playlists_dir=self.app_state.playlists_dir,
            parent=self,
        )
        # playlists pages
        self.playlist_detail_window = PlaylistDetailWindow(self)
        self.playlist_detail_window.set_app_state(self.app_state)

        # Register PlaylistDetailWindow in stackedWidget (hidden from nav)
        self.addSubInterface(
            self.playlist_detail_window,
            FIF.MUSIC,
            "PlaylistDetail",
            NavigationItemPosition.SCROLL,
        )
        # Hide its nav item — access is programmatic only
        try:
            self.navigationInterface.widget("PlaylistDetailWindow").hide()
        except Exception:
            pass

        # dynamic playlist items in SCROLL
        self._playlist_nav_widgets: list[str] = []
        self.__rebuild_playlist_navigation()


    def __create_windows(self) -> None:
        """Create objects of classes /windows."""
        self.home_window = HomeWindow(self.app_state, self)
        self.settings_window = SettingsWindow(self.app_state, self)


    def __connect_signals(self) -> None:
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
        
        # Signals PlaylistManager -> MainFluentWindow
        self.playlist_manager.playlists_changed.connect(self.__rebuild_playlist_navigation)

        # Signals PlaylistDetailWindow -> AudioPlayerController
        self.playlist_detail_window.play_track_requested.connect(self._play_playlist_track)
        
        # Signals PlaylistDetailWindow -> MainFluentWindow
        self.playlist_detail_window.back_requested.connect(self._on_playlist_detail_back)
        self.playlist_detail_window.add_to_playlist_requested.connect(self._on_add_to_playlist)

        # Signals PlaylistDetailWindow -> PlaylistManager
        self.playlist_detail_window.add_tracks_confirmed.connect(
            lambda pid, paths: self.playlist_manager.add_tracks_to_playlist(pid, paths)
        )
        self.playlist_detail_window.remove_track_requested.connect(
            lambda pid, idx: self.playlist_manager.remove_track_from_playlist(pid, idx)
        )
        self.playlist_detail_window.reorder_requested.connect(
            lambda pid, f, t: self.playlist_manager.move_track_in_playlist(pid, f, t)
        )

        # Signals PlaylistManager → PlaylistDetailWindow
        self.playlist_manager.playlist_updated.connect(self._on_playlist_updated)

        # Signals SongListItem → HomeWindow -> MainFluentWindow
        self.home_window.add_to_playlist_requested.connect(self._on_add_to_playlist)

        # Signals AudioPlayerController -> PlaylistDetailWindow
        self.audio_player.trackChanged.connect(self.playlist_detail_window.highlight_current_track)

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


    def __rebuild_playlist_navigation(self) -> None:
        """Rebuild the scrollable navigation section for the current playlist list."""
        # Delete old objects
        for widget_id in self._playlist_nav_widgets:
            try:
                self.navigationInterface.removeItem(widget_id)
            except Exception:
                pass
        self._playlist_nav_widgets.clear()

        # Add new objects
        for playlist in self.playlist_manager.get_all_playlists():
            nav_id = f"playlist_{playlist.id}"
            self.navigationInterface.addItem(
                routeKey=nav_id,
                icon=FIF.MUSIC,
                text=playlist.name,
                onClick=lambda checked, pid=playlist.id: self.__on_nav_playlist_clicked(pid),
                position=NavigationItemPosition.SCROLL,
                tooltip=playlist.name,
            )
            self._playlist_nav_widgets.append(nav_id)


    def __on_nav_playlist_clicked(self, playlist_id: str) -> None:
        """Click a playlist in the navigation → open its contents."""
        playlist = self.playlist_manager.get_playlist(playlist_id)
        if playlist:
            self.playlist_detail_window.set_playlist(playlist)
            # Switch stackedWidget directly (playlist_detail_window is hidden in nav)
            self.stackedWidget.setCurrentWidget(self.playlist_detail_window)


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


    def _on_create_playlist(self) -> None:
        """Open the playlist creation dialog."""
        dialog = CreatePlaylistDialog(parent=self)
        dialog.playlist_confirmed.connect(self._on_playlist_created)
        dialog.exec()


    def _on_playlist_created(self, name: str, color: str) -> None:
        """Playlist created → refresh navigation and list."""
        self.playlist_manager.create_playlist(name, color)


    def _on_edit_playlist(self, playlist_id: str) -> None:
        """Open the playlist editing dialog."""
        playlist = self.playlist_manager.get_playlist(playlist_id)
        if playlist is None:
            return
        dialog = CreatePlaylistDialog(
            existing_name=playlist.name,
            existing_color=playlist.color,
            parent=self,
        )
        dialog.playlist_confirmed.connect(
            lambda n, c: self.playlist_manager.rename_playlist(playlist_id, n, c)
        )
        dialog.exec()


    def _on_delete_playlist(self, playlist_id: str) -> None:
        """Delete playlist."""
        self.playlist_manager.delete_playlist(playlist_id)


    def _on_add_to_playlist(self, track_path: Path, pos) -> None:
        """Open the 'Add to playlist' dialog for a single track."""
        playlists = self.playlist_manager.get_all_playlists()
        if not playlists:
            # if playlists doesn't exists -> create one.
            self._on_create_playlist()
            return

        dialog = AddToPlaylistDialog(playlists, parent=self)
        dialog.confirmed.connect(
            lambda ids: self.playlist_manager.add_tracks_to_playlists([track_path], ids)
        )
        dialog.new_playlist_requested.connect(self._on_create_playlist)
        dialog.exec()


    def _on_playlist_detail_back(self) -> None:
        """'Back' button in PlaylistDetailWindow → return to Home."""
        self.switchTo(self.home_window)


    def _on_playlist_updated(self, playlist_id: str) -> None:
        """Playlist updated → if open, redraw."""
        if self.playlist_detail_window._playlist and \
           self.playlist_detail_window._playlist.id == playlist_id:
            playlist = self.playlist_manager.get_playlist(playlist_id)
            if playlist:
                self.playlist_detail_window.set_playlist(playlist)

    def _play_playlist_track(self, path: Path, paths: list) -> None:
        """Play a track from a playlist, setting the playlist as the current queue."""
        self.app_state.playlist_paths = paths
        self.audio_player._play_file(path)
