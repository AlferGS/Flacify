#core/audio_player_conroller.py
import os
import time
from pathlib import Path
from random import shuffle

import app

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "HIDE"

from pygame import USEREVENT, display, event as pg_event, mixer
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from .metadata_reader import MetadataReader
from .app_state import AppState

# Custom Event for track end (also play/stop)
TRACK_END_EVENT = USEREVENT + 1

class AudioPlayerController(QObject):
    playbackStateChanged = pyqtSignal(bool) # True = Playing, False = Paused/Stopped
    shuffleButtonEnabled = pyqtSignal(bool) # is shuffle Button Enabled
    trackChanged = pyqtSignal(str, str, str, object)  #title, artist, album, cover_data
    trackSliderChanged = pyqtSignal(int, int) # current_ms, total_ms
    sessionRestored = pyqtSignal(str, str, str, object) # title, artist, album, cover_data


    def __init__(self, playlist:list[Path]=None, app_state: AppState = None, parent=None) -> None:
        super().__init__(parent)
        self.app_state = app_state
        self.current_playlist = playlist if playlist else []
        self._current_track_index = 0
        self._play_start_time = 0.0
        self._play_start_position_ms = 0
        self._pause_position_ms = 0
        self._total_duration_ms = 0
        self._current_volume = 0.25
        self.is_playing = False
        self.is_paused = False
        self.is_muted = False
        self.is_album_loop = False
        self.message = ""
        # TODO: Обновить переменные исходя из того что имеется доступ к app_state
        
        if not mixer.get_init():
            mixer.init()
        if not display.get_init():
            display.init()

        mixer.music.set_endevent(TRACK_END_EVENT)

        # Restore volume from AppState
        if self.app_state:
            self._current_volume = self.app_state.volume
            self._apply_volume()
            print(f"[AudioPlayer] Restore volume: {self._current_volume}")

        self._event_timer = QTimer(self)
        self._event_timer.timeout.connect(self.update)
        self._event_timer.start(100)

        if self.app_state and self.app_state.playlist_paths:
            self._restore_playlist_from_state()


    @property
    def current_track_index(self) -> int:
        return self._current_track_index

    @current_track_index.setter
    def current_track_index(self, index:int) -> None:
        if 0 <= index < len(self.current_playlist):
            self._current_track_index = index
        else:
            self.message = "Index out of range"


    def restore_last_session(self) -> bool:
        """
        Try to restore data about last track before closing app.
        Load file in mixer and update metadata, but do not playing it.
        Return True, if restoring was successful.
        """
        if not self.app_state or not self.app_state.current_track_path:
            return False
            
        file_path = Path(self.app_state.current_track_path)
        if not file_path.exists():
            return False

        try:
            mixer.music.load(str(file_path))
            mixer.music.play()
            mixer.music.pause()
            
            self.is_playing = True
            self.is_paused = True
            
            self.playbackStateChanged.emit(True)
            
            meta = MetadataReader.get_metadata(file_path)
            self.trackChanged.emit(meta["title"], meta["artist"], meta["album"], meta["cover_data"])
            
            self._total_duration_ms = self._get_duration_ms(file_path)
            self._play_start_time = time.time()
            self._play_start_position_ms = 0
            
            has_next = self._current_track_index < len(self.current_playlist) - 1
            self.shuffleButtonEnabled.emit(has_next)
            
            print("[AudioPlayer] Сессия восстановлена (Pause)")
            return True
        except Exception as e:
            print(f"[AudioPlayer] Error restoring session: {e}")
            return False



    def _restore_playlist_from_state(self):
        """Загружает плейлист из AppState в текущий объект."""
        try:
            paths = [Path(p) for p in self.app_state.playlist_paths if Path(p).exists()]
            if paths:
                self.current_playlist = paths
                # Индекс восстанавливается из state
                idx = self.app_state.current_track_index
                if 0 <= idx < len(self.current_playlist):
                    self._current_track_index = idx
                    print(f"[AudioPlayer] Плейлист восстановлен: {len(paths)} треков")
        except Exception as e:
            print(f"[AudioPlayer] Ошибка восстановления плейлиста: {e}")


    def set_playlist(self, playlist: list[Path], start_index: int = 0) -> None:
        """Устанавливает новый плейлист и начинает воспроизведение."""
        if not playlist:
            return
            
        self.current_playlist = playlist
        self._current_track_index = start_index
        
        # Сохраняем состояние плейлиста в AppState (в память)
        if self.app_state:
            current_track = self.current_playlist[self._current_track_index]
            self.app_state.save_playlist_state(self.current_playlist, self._current_track_index, current_track)
            
        self.play_current_track()
    

    def set_playlist(self, playlist: list[Path], start_index: int=0) -> None:
        """ Safety change playlist
        Args:
            playlist (list[Path]): new playlist
            start_index (int, optional): new index of song. Defaults to 0.
        """
        self.current_playlist = playlist
        self.current_track_index = start_index
        if self.current_playlist:
            self.play_current_track()


    def get_song_name(self) -> str:
        """ Return song name
        Returns:
            str: song name
        """
        return self.current_playlist[self.current_track_index].name


    def next_track(self) -> None:
        """ Skip to next track
        Increment index of current_track index to += 1 
        """
        next_idx = self._current_track_index + 1

        if next_idx >= len(self.current_playlist):
            if self.is_album_loop:
                self._current_track_index = 0
                self.play_current_track()
    
            else:
                self.message = "End of album"
        else:
            self._current_track_index = next_idx
            self.play_current_track()


    def prev_track(self):
        """ Skip to previous track
        Decrement index of current_track index to -= 1 
        """
        # print("prev_track")
        prev_idx = self._current_track_index - 1

        if prev_idx < 0:
            if self.is_album_loop:
                self._current_track_index = len(self.current_playlist) - 1
                self.play_current_track()
            else:
                self.message = "Start of album"
                self._current_track_index = 0
                mixer.music.rewind()
                self._play_start_time = time.time()
                self._play_start_position_ms = 0
        else:
            self._current_track_index = prev_idx
            self.play_current_track()


    def play_current_track(self) -> None:
        """ Start play track
        Use current_track_index to path from current_playlist[]
        """
        if not self.current_playlist:
            return
        
        file_path = self.current_playlist[self._current_track_index]
        
        try:
            mixer.music.load(str(file_path))
            mixer.music.play()
            
            self.is_playing = True
            self.is_paused = False
            
            # >>> ЭМИТИМ СОСТОЯНИЕ PLAY
            self.playbackStateChanged.emit(True)
            
            # Метаданные
            meta = MetadataReader.get_metadata(file_path)
            self.trackChanged.emit(meta["title"], meta["artist"], meta["album"], meta["cover_data"])
            
            # Длительность
            self._total_duration_ms = self._get_duration_ms(file_path)
            self._play_start_time = time.time()
            self._play_start_position_ms = 0
            
            # Shuffle button logic
            has_next = self._current_track_index < len(self.current_playlist) - 1
            self.shuffleButtonEnabled.emit(has_next)
            
        except Exception as e:
            print(f"Error playing: {e}")
            self.next_track()


    def pause_track(self):
        if not self.current_playlist:
            return

        if self.is_playing and not self.is_paused:
            mixer.music.pause()
            self.is_paused = True
            self._pause_position_ms = self._get_current_position_ms()
            self.playbackStateChanged.emit(False)
        else:
            mixer.music.unpause()
            self.is_paused = False
            self._play_start_time = time.time()
            self._play_start_position_ms = self._pause_position_ms
            self.playbackStateChanged.emit(True)
        

    def toggle_mute(self) -> bool:
        """Toggle state mute. Return new value is_muted."""
        self.is_muted = not self.is_muted
        self._apply_volume()
        return self.is_muted


    def set_volume(self, volume: float):
        """Set volume (0.0 - 1.0). Auto sync is_muted."""
        self._current_volume = max(0.0, min(1.0, volume))
        self.is_muted = (self._current_volume == 0.0)
        self._apply_volume()

        if self.app_state:
            self.app_state.volume = self._current_volume


    def _apply_volume(self):
        """Set new volume in accordance with is_muted flag."""
        if self.is_muted:
            mixer.music.set_volume(0.0)
        else:
            mixer.music.set_volume(self._current_volume)

        
    def is_end_of_track(self):
        return not self.is_playing and not self.is_paused
    

    def shuffle_playlist(self) -> None:
        print("before:")
        print(*self.current_playlist, sep='\n')
        temp_playlist = self.current_playlist[self.current_track_index+1:]
        shuffle(temp_playlist)
        self.current_playlist[self.current_track_index+1:] = temp_playlist
        print("after:")
        print(*self.current_playlist, sep='\n')
        print('--------------------------------')


    def _get_duration_ms(self, file_path: Path) -> int:
        """ Get track duration in ms from mutagen
        """
        try:
            import mutagen
            audio = mutagen.File(file_path)
            if audio and audio.info:
                return int(audio.info.length * 1000)
        except Exception:
            pass
        return 0
    
    
    def _get_current_position_ms(self) -> int:
        """
        Вычисляет реальную позицию воспроизведения на основе системного времени.
        Не зависит от капризного поведения pygame.mixer.music.get_pos().
        """
        if not self.is_playing:
            return 0
        elapsed_ms = (time.time() - self._play_start_time) * 1000
        current = self._play_start_position_ms + elapsed_ms
        if current > self._total_duration_ms:
            current = self._total_duration_ms
        return int(current)
    

    def seek(self, position_ms: int):
        try:
            if position_ms < 0:
                position_ms = 0
            if position_ms > self._total_duration_ms:
                position_ms = self._total_duration_ms

            # --------Изменение номер 7-----------------------------------------------
            """ Обновляем таймеры вместе с seek, чтобы позиция считалась от новой точки.
            Было: self._seek_offset_ms = position_ms
            """
            mixer.music.set_pos(position_ms / 1000.0)
            self._play_start_time = time.time()
            self._play_start_position_ms = position_ms
            # -------------------------------------------------------------------------------
        except Exception as e:
            print(f"Seek error: {e}")


    def update(self):
        """
        Этот метод должен вызываться регулярно в основном цикле приложения.
        Он проверяет очередь событий pygame и реагирует на окончание трека.
        """
        for evt in pg_event.get():
            if evt.type == TRACK_END_EVENT and not self.is_paused:
                self.message = "Its track end event"
                self.is_playing = False
                self.next_track()
                break 
        
        if self.is_playing and not self.is_paused and self.current_playlist:
            current_ms = self._get_current_position_ms()
            self.trackSliderChanged.emit(current_ms, self._total_duration_ms)