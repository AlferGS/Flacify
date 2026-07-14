#core/audio_player_conroller.py
import os
import time
from pathlib import Path
from random import shuffle
from mutagen import File

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "HIDE"

from pygame import USEREVENT, display, event as pg_event, mixer
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from .metadata_reader import MetadataReader
from .app_state import AppState
from .repeat_mode import RepeatMode

# Custom Event for track end (also play/stop)
TRACK_END_EVENT = USEREVENT + 1


class AudioPlayerController(QObject):
    playbackStateChanged = pyqtSignal(bool) # True = Playing, False = Paused/Stopped
    shuffleButtonEnabled = pyqtSignal(bool) # is shuffle Button Enabled
    trackChanged = pyqtSignal(str, str, str, object)  #title, artist, album, cover_data
    trackSliderChanged = pyqtSignal(int, int) # current_ms, total_ms
    sessionRestored = pyqtSignal(str, str, str, object) # title, artist, album, cover_data
    repeatModeChanged = pyqtSignal(RepeatMode)
    updateShuffledPlaylist = pyqtSignal()


    def __init__(self, app_state: AppState = None, parent=None) -> None:
        """Init variables, mixer, restore parameters from last session."""
        super().__init__(parent)
        self.app_state = app_state
        self._play_start_time = 0.0
        self._play_start_position_ms = 0
        self._pause_position_ms = 0
        self._total_duration_ms = 0
        self.is_playing = False
        self.is_paused = False
        self.is_muted = False
        self.is_repeated: RepeatMode = RepeatMode.OFF
        
        if not mixer.get_init():
            mixer.init()
        if not display.get_init():
            display.init()

        mixer.music.set_endevent(TRACK_END_EVENT)

        self._event_timer = QTimer(self)
        self._event_timer.timeout.connect(self.update)
        self._event_timer.start(250)

        # Restore volume and playlist from AppState
        if self.app_state and self.app_state.playlist_paths:
            self.__apply_volume()
        

    def __apply_volume(self):
        """Set new volume in accordance with is_muted flag."""
        if self.is_muted:
            mixer.music.set_volume(0.0)
        else:
            mixer.music.set_volume(self.app_state.volume)
    

    def __get_duration_ms(self, file_path: Path) -> int:
        """ Get track duration in ms from mutagen."""
        try:
            audio = File(file_path)
            if audio and audio.info:
                return int(audio.info.length * 1000)
        except Exception:
            pass
        return 0
    
    
    def __get_current_position_ms(self) -> int:
        """Calculates the actual playback position based on the system time."""
        if not self.is_playing:
            return 0
        elapsed_ms = (time.time() - self._play_start_time) * 1000
        current = self._play_start_position_ms + elapsed_ms
        if current > self._total_duration_ms:
            current = self._total_duration_ms
        return int(current)
    

    def __on_track_finished(self) -> None:
        """
        Called when a track has played to its natural end.
        Decides what to do next based on the current RepeatMode.
        """
        playlist = self.app_state.playlist_paths
        if not playlist:
            return

        if self.is_repeated == RepeatMode.SONG_LOOP:
            self._play_current_track()
            return

        if self.is_repeated == RepeatMode.ALBUM_LOOP:
            self._next_track()
            return

        if self.app_state.current_track_index >= len(playlist) - 1:
            self.playbackStateChanged.emit(False)
            return

        self._next_track()


    def _restore_last_session(self) -> bool:
        """
        Try to restore data about last track before closing app.
        Load file in mixer and update metadata, but do not playing it.
        Return True, if restoring was successful.
        """
        if not self.app_state or not self.app_state.current_track_path.exists():
            return False
            
        try:
            mixer.music.load(str(self.app_state.current_track_path))
            mixer.music.play()
            mixer.music.pause()
            
            self.is_playing = True
            self.is_paused = True
            
            self.playbackStateChanged.emit(True)
            
            meta = MetadataReader.get_metadata(self.app_state.current_track_path)
            self.trackChanged.emit(meta["title"], meta["artist"], meta["album"], meta["cover_data"])
            
            self._total_duration_ms = self.__get_duration_ms(self.app_state.current_track_path)
            self._play_start_time = time.time()
            self._play_start_position_ms = 0
            
            has_next = self.app_state.current_track_index < len(self.app_state.playlist_paths) - 1
            self.shuffleButtonEnabled.emit(has_next)
            
            return True
        except Exception as e:
            print(f"[AudioPlayer] Error restoring session: {e}")
            return False


    def _next_track(self) -> None:
        """ Skip to next track.
        Increment index of current_track index to += 1 
        """
        if not self.app_state.playlist_paths:
            return
        
        next_idx = self.app_state.current_track_index + 1

        if next_idx >= len(self.app_state.playlist_paths):
            if self.is_repeated == RepeatMode.ALBUM_LOOP:
                next_idx = 0
            else:
                return

        self.app_state.current_track_index = next_idx
        self.app_state.current_track_path = self.app_state.playlist_paths[next_idx]
        self._play_current_track()


    def _prev_track(self) -> None:
        """ Skip to previous track.
        Decrement index of current_track index to -= 1 
        """
        if not self.app_state.playlist_paths:
            return

        prev_idx = self.app_state.current_track_index - 1

        if prev_idx < 0:
            if self.is_repeated == RepeatMode.ALBUM_LOOP:
                prev_idx = len(self.app_state.playlist_paths) - 1
                self.app_state.current_track_index = prev_idx
                self.app_state.current_track_path = self.app_state.playlist_paths[prev_idx]
                self._play_current_track()
            else:
                # OFF / SONG_LOOP — stay on the first track, rewind to the beginning
                self.app_state.current_track_index = 0
                self.app_state.current_track_path = self.app_state.playlist_paths[0]
                mixer.music.rewind()
                self._play_start_time = time.time()
                self._play_start_position_ms = 0
        else:
            self.app_state.current_track_index = prev_idx
            self.app_state.current_track_path = self.app_state.playlist_paths[prev_idx]
            self._play_current_track()


    def _get_playlist_index(self, path: Path) -> int | None:
        """Return the index of a path in the current playlist, if present."""
        playlist = self.app_state.playlist_paths
        for index, candidate in enumerate(playlist):
            if candidate == path:
                return index
        return None


    def _play_current_track(self) -> None:
        """ Start play track.
        Use current_track_index to path from app_state.playlist_paths[]
        """
        if not self.app_state.playlist_paths:
            return
        
        try:
            mixer.music.load(str(self.app_state.current_track_path))
            mixer.music.play()
        except Exception as e:
            print(f"[AudioPlayer] Error playing track {self.app_state.current_track_path}: {e}")
            self.is_playing = False
            self.is_paused = False
            self._play_start_time = 0.0
            self._play_start_position_ms = 0
            self._pause_position_ms = 0
            self._total_duration_ms = 0
            self.playbackStateChanged.emit(False)
            return

        self.is_playing = True
        self.is_paused = False

        self.playbackStateChanged.emit(True)

        meta = MetadataReader.get_metadata(self.app_state.current_track_path)
        self.trackChanged.emit(meta["title"], meta["artist"], meta["album"], meta["cover_data"])

        self._total_duration_ms = self.__get_duration_ms(self.app_state.current_track_path)
        self._play_start_time = time.time()
        self._play_start_position_ms = 0

        has_next = self.app_state.current_track_index < len(self.app_state.playlist_paths) - 1
        self.shuffleButtonEnabled.emit(has_next or self.is_repeated == RepeatMode.ALBUM_LOOP)

    
    def _play_file(self, path: Path) -> None:
        """Starts playback of the specified file."""
        track_index = self._get_playlist_index(path)
        if track_index is not None:
            self.app_state.current_track_index = track_index
            self.app_state.current_track_path = path
            self._play_current_track()
        else:
            print(f"Track {path} not found in playlist")


    def _pause_track(self) -> None:
        """Toggle track pause/unpause."""
        if not self.app_state.playlist_paths:
            return

        if self.is_playing and not self.is_paused:
            mixer.music.pause()
            self.is_paused = True
            self._pause_position_ms = self.__get_current_position_ms()
            self.playbackStateChanged.emit(False)
        else:
            mixer.music.unpause()
            self.is_paused = False
            self._play_start_time = time.time()
            self._play_start_position_ms = self._pause_position_ms
            self.playbackStateChanged.emit(True)
        

    def _toggle_mute(self) -> bool:
        """Toggle mute state. Return new value is_muted."""
        self.is_muted = not self.is_muted
        self.__apply_volume()
        return self.is_muted
    

    def _toggle_repeat(self):
        """Toggle repeat state."""
        self.is_repeated = self.is_repeated.next()
        self.repeatModeChanged.emit(self.is_repeated)


    def _set_volume(self, volume: float):
        """Set volume (0.0 - 1.0). Auto sync is_muted."""
        self.app_state.volume = max(0.0, min(1.0, volume))
        self.is_muted = (self.app_state.volume == 0.0)
        self.__apply_volume()


    def _shuffle_playlist(self) -> None:
        full_playlist = self.app_state.playlist_paths
        if not full_playlist or self.app_state.current_track_index >= len(full_playlist):
            return
        
        tail_to_shuffle = full_playlist[self.app_state.current_track_index+1:]
        shuffle(tail_to_shuffle)
        full_playlist[self.app_state.current_track_index+1:] = tail_to_shuffle

        self.app_state.playlist_paths = full_playlist
        self.updateShuffledPlaylist.emit()


    def _update_queue_order(self, new_order: list[Path]) -> None:
        """Update index of current_track in app_state"""
        current_path = self.app_state.current_track_path
        
        if not current_path or not current_path.exists():
            return
            
        try:
            new_index = new_order.index(current_path) # new index of current track
                        
            self.app_state.current_track_index = new_index
            print(f"[AudioPlayer] Queue reordered. New current index: {new_index}")
            
            has_next = new_index < len(new_order) - 1
            self.shuffleButtonEnabled.emit(has_next or self.is_repeated == RepeatMode.ALBUM_LOOP)
            
        except ValueError:
            print("[AudioPlayer] Warning: Current track not found in new queue order.")


    def _seek(self, position_ms: int):
        """This method implements rewinding of an audio track
        to the specified position in milliseconds."""
        try:
            if position_ms < 0:
                position_ms = 0
            if position_ms > self._total_duration_ms:
                position_ms = self._total_duration_ms

            mixer.music.set_pos(position_ms / 1000.0)
            self._play_start_time = time.time()
            self._play_start_position_ms = position_ms
        except Exception as e:
            print(f"Seek error: {e}")


    def update(self):
        """
        This method should be called regularly in the application's main loop.
        It checks the pygame event queue and responds to the end of a track.
        """
        for evt in pg_event.get():
            if evt.type == TRACK_END_EVENT and not self.is_paused:
                self.is_playing = False
                self.__on_track_finished()
                break 
        
        if self.is_playing and not self.is_paused and self.app_state.playlist_paths:
            current_ms = self.__get_current_position_ms()
            self.trackSliderChanged.emit(current_ms, self._total_duration_ms)
