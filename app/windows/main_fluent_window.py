#windows/main_fluent_window.py
import os
from pathlib import Path
os.environ['QFLUENT_WIDGETS_PRO_TIPS'] = '0'
from random import shuffle

from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtGui import QCloseEvent, QIcon
from qfluentwidgets import (
    FluentIcon as FIF,
    FluentWindow,
    IconWidget,
    NavigationItemPosition,
    Theme,
    setTheme,
    MessageBox,
)
from .home_window import HomeWindow
from .settings_window import SettingsWindow
from app.core import AudioPlayerController, FileBrowserModel, AppState
from app.core.playlist_manager import PlaylistManager
# from app.core.playlist import Playlist
from app.components.create_playlist_dialog import CreatePlaylistDialog
from app.components.add_to_playlist_dialog import AddToPlaylistDialog
from app.components.playlist_nav_item import PlaylistNavItem

# Display size of the playlist badge in the navigation panel
NAV_BADGE_SIZE = 36

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
        self.playlist_manager = PlaylistManager(
            playlists_dir=self.app_state.playlists_dir,
            parent=self,
        )
        self._playlist_nav_widgets: list[str] = []
        self._playlist_nav_items: dict = {}
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

        # Signals SettingsWindow -> HomeWindow/FileBrowserModel
        self.settings_window.root_path_changed.connect(self.home_window.show_browser)
        
        # Signals QueueWindow -> AudioPlayerController
        self.home_window.queue_window.queue_reordered.connect(self.audio_player._update_queue_order)
        self.home_window.queue_window.play_track_requested.connect(self.audio_player._play_at_index)
        
        # Signals FileBrowserModel -> HomeWindow
        self.file_browser.directoryLoaded.connect(self.home_window._onDirectoryLoaded)
        self.file_browser.directoryChanged.connect(self.home_window.requestDirectory)
        
        # Signals FileBrowserModel -> AudioPlayerController
        self.file_browser.playbackStarted.connect(self.audio_player._play_current_track)
        self.file_browser.nextTrack.connect(self.audio_player._next_track)
        self.file_browser.prevTrack.connect(self.audio_player._prev_track)
        
        # Signals PlaylistManager -> MainFluentWindow
        self.playlist_manager.playlists_changed.connect(self.__rebuild_playlist_navigation)
       
        # Signals HomeWindow (playlist mode) -> MainFluentWindow
        self.home_window.playlist_track_clicked.connect(self._play_playlist_track)
        self.home_window.playlist_remove_track_requested.connect(
            lambda pid, idx: self.playlist_manager.remove_track_from_playlist(pid, idx)
        )
        
        self.home_window.playlist_add_tracks_requested.connect(self._on_playlist_add_tracks)
        self.home_window.playlist_reorder_requested.connect(
            lambda pid, f, t: self.playlist_manager.move_track_in_playlist(pid, f, t)
        )
        self.home_window.playlist_play_requested.connect(self._on_playlist_play)
        self.home_window.playlist_shuffle_requested.connect(self._on_playlist_shuffle)
        self.home_window.playlist_edit_requested.connect(self._on_edit_playlist)
        self.home_window.playlist_delete_requested.connect(self._on_playlist_delete)
        
        # Signals PlaylistManager -> HomeWindow (playlist mode)
        self.playlist_manager.playlist_updated.connect(self._on_playlist_updated)
        
        # Signals SongListItem -> HomeWindow -> MainFluentWindow
        self.home_window.add_to_playlist_requested.connect(self._on_add_to_playlist)
        
        # Signals AudioPlayerController -> HomeWindow (playlist highlight)
        self.audio_player.trackChanged.connect(self.home_window.highlight_playlist_track)

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
        # Delete old objects; ids that failed to remove are kept for retry
        not_removed = []
        for widget_id in self._playlist_nav_widgets:
            if not self.__remove_nav_widget(widget_id):
                not_removed.append(widget_id)
        self._playlist_nav_widgets = not_removed
        self._playlist_nav_items.clear()
        # Add new objects via the official addWidget API (no monkey-patch).
        # Signature (verified): addWidget(routeKey, widget: NavigationWidget,
        #   onClick=None, position=TOP, tooltip=None, parentRouteKey=None)
        for playlist in self.playlist_manager.get_all_playlists():
            nav_id = f"playlist_{playlist.id}"
            item = PlaylistNavItem(playlist, badge_size=NAV_BADGE_SIZE)
            self.navigationInterface.addWidget(
                nav_id,
                item,
                onClick=lambda *_, pid=playlist.id: self.__on_nav_playlist_clicked(pid),
                position=NavigationItemPosition.SCROLL,
                tooltip=playlist.name,
            )
            self._playlist_nav_widgets.append(nav_id)
            self._playlist_nav_items[nav_id] = item


    def __remove_nav_widget(self, route_key: str) -> bool:
        """Remove a navigation item by routeKey (version-safe). Return True if removed."""
        try:
            if hasattr(self.navigationInterface, "removeWidget"):
                self.navigationInterface.removeWidget(route_key)
            elif hasattr(self.navigationInterface, "removeItem"):
                self.navigationInterface.removeItem(route_key)
            else:
                return False
            return True
        except Exception as e:
            print(f"[MainFluentWindow] Failed to remove nav item {route_key}: {e}")
            return False


    def switchTo(self, widget) -> None:
        """Override: navigating to Home while a playlist is open returns to browser.
        Programmatic playlist opening bypasses this via stackedWidget.setCurrentWidget,
        so the playlist nav item stays highlighted and the mode is not reset."""
        if widget is self.home_window:
            self.home_window.reset_to_browser_if_playlist()
        super().switchTo(widget)

    def __on_nav_playlist_clicked(self, playlist_id: str) -> None:
        """Click a playlist in the navigation → show it inside HomeWindow.
        Uses setCurrentWidget (NOT switchTo) so the playlist nav item stays
        selected and the browser-reset hook in switchTo is not triggered."""
        playlist = self.playlist_manager.get_playlist(playlist_id)
        if playlist:
            self.home_window.show_playlist(playlist)
            self.stackedWidget.setCurrentWidget(self.home_window)


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


    def _on_playlist_add_tracks(self, playlist_id: str) -> None:
        """Open file dialog and add selected tracks to playlist."""
        extensions = " ".join(
            f"*{ext}" for ext in sorted(
                {".flac", ".mp3", ".wav", ".ogg", ".aac", ".m4a", ".wma"}
            )
        )
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add tracks to playlist", "", f"Audio files ({extensions})"
        )
        if files:
            paths = [Path(f) for f in files]
            self.playlist_manager.add_tracks_to_playlist(playlist_id, paths)


    def _on_playlist_play(self, playlist_id: str) -> None:
        """Green play button: always start playlist from the first track."""
        playlist = self.playlist_manager.get_playlist(playlist_id)
        if not playlist or not playlist.tracks:
            return
        paths = playlist.track_paths
        self._play_playlist_track(0, paths)


    def _on_playlist_shuffle(self, playlist_id: str) -> None:
        """Shuffle button: shuffle playlist tracks and start from a random first."""
        playlist = self.playlist_manager.get_playlist(playlist_id)
        if not playlist or not playlist.tracks:
            return
        paths = playlist.track_paths
        shuffle(paths)
        self._play_playlist_track(0, paths)


    def _on_playlist_delete(self, playlist_id: str) -> None:
        """Delete playlist with confirmation; return to browser and refresh nav."""
        playlist = self.playlist_manager.get_playlist(playlist_id)
        if playlist is None:
            return
        box = MessageBox(
            "Delete playlist",
            f"Playlist '{playlist.name}' will be permanently deleted.",
            self,
        )
        box.yesButton.setText("Delete")
        box.cancelButton.setText("Cancel")
        if not box.exec():
            return
        # If the deleted playlist is open — return HomeWindow to browser mode
        if self.home_window.is_showing_playlist(playlist_id):
            self.home_window.show_browser()
        # Move navigation focus to Home BEFORE removing the nav item
        self.switchTo(self.home_window)
        # delete_playlist emits playlists_changed, which already rebuilds navigation.
        self.playlist_manager.delete_playlist(playlist_id)


    def _on_add_to_playlist(self, track_path: Path, pos) -> None:
        """Open the 'Add to playlist' dialog for a single track."""
        playlists = self.playlist_manager.get_all_playlists()
        if not playlists:
            # No playlists yet: create one first, then open the dialog with it pre-checked
            self._create_playlist_then_add(track_path)
            return
        self._open_add_to_playlist_dialog(track_path, playlists)


    def _open_add_to_playlist_dialog(
        self,
        track_path: Path,
        playlists: list,
        checked_ids: set = None,
    ) -> None:
        """Build and show AddToPlaylistDialog; '+ New playlist' refreshes the list in place."""
        dialog = AddToPlaylistDialog(playlists, parent=self, checked_ids=checked_ids)
        dialog.confirmed.connect(
            lambda ids: self.playlist_manager.add_tracks_to_playlists([track_path], ids)
        )
        dialog.new_playlist_requested.connect(
            lambda: self._on_new_playlist_from_add_dialog(dialog)
        )
        dialog.exec()


    def _on_new_playlist_from_add_dialog(self, dialog) -> None:
        """'+ New playlist' inside the add dialog: create and refresh the list with the new row checked."""
        creator = CreatePlaylistDialog(parent=self)

        def _on_confirmed(name: str, color: str) -> None:
            new_id = self.playlist_manager.create_playlist(name, color)
            dialog.refresh_playlists(
                self.playlist_manager.get_all_playlists(),
                checked_ids={new_id},
            )

        creator.playlist_confirmed.connect(_on_confirmed)
        creator.exec()


    def _create_playlist_then_add(self, track_path: Path) -> None:
        """No playlists exist: create one, then open the add dialog with it pre-checked."""
        creator = CreatePlaylistDialog(parent=self)

        def _on_confirmed(name: str, color: str) -> None:
            new_id = self.playlist_manager.create_playlist(name, color)
            self._open_add_to_playlist_dialog(
                track_path,
                self.playlist_manager.get_all_playlists(),
                checked_ids={new_id},
            )

        creator.playlist_confirmed.connect(_on_confirmed)
        creator.exec()


    def _on_playlist_updated(self, playlist_id: str) -> None:
        """Playlist updated → refresh HomeWindow view and the nav row (rename/recolor)."""
        playlist = self.playlist_manager.get_playlist(playlist_id)
        if playlist is None:
            return
        self.home_window.update_playlist_view(playlist)
        self.__update_nav_playlist_item(playlist)


    def __update_nav_playlist_item(self, playlist) -> None:
        """Update a single navigation row in place via our own registry."""
        nav_id = f"playlist_{playlist.id}"
        item = self._playlist_nav_items.get(nav_id)
        if item is not None:
            item.update_playlist(playlist)


    def _play_playlist_track(self, track_index: int, paths: list) -> None:
        """Play a track from a playlist by position, setting the playlist as current queue."""
        self.app_state.playlist_paths = paths
        self.audio_player._play_at_index(track_index)
