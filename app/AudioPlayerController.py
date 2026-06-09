import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "HIDE"
from pathlib import Path
from pygame import (
    display,
    mixer, 
    USEREVENT,
    event as pg_event,
    error as pyerror
)
from PyQt5.QtCore import QObject, pyqtSignal

# Custom Event for track end (also play/stop)
TRACK_END_EVENT = USEREVENT + 1

class AudioPlayerController(QObject):
    def __init__(self, playlist:list[Path], parent=None) -> None:
        super().__init__(parent)
        self.current_playlist = playlist
        self._current_track_index = 0
        self.is_playing = False
        self.is_album_loop = False
        self.message = ""
        
        if not mixer.get_init():
            mixer.init()
        if not display.get_init():
            display.init()

        mixer.music.set_endevent(TRACK_END_EVENT)
        mixer.music.set_volume(0.15)

        self.message = f"AudioPlayer created with {len(self.current_playlist)} tracks"


    @property
    def current_track_index(self) -> int:
        return self._current_track_index


    @current_track_index.setter
    def current_track_index(self, index:int) -> None:
        if 0 <= index < len(self.current_playlist):
            self._current_track_index = index
        else:
            self.message = "Index out of range"

    
    def get_song_name(self) -> str:
        return self.current_playlist[self.current_track_index].name


    def next_track(self):
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
        prev_idx = self._current_track_index - 1

        if prev_idx < 0:
            if self.is_album_loop:
                self._current_track_index = len(self.current_playlist) - 1
                self.play_current_track()
            else:
                self.message = "Start of album"
                self._current_track_index = 0
                mixer.music.rewind()
        else:
            self._current_track_index = prev_idx
            self.play_current_track()


    def play_current_track(self) -> None:
        if not self.current_playlist:
            return
        
        file_path = self.current_playlist[self._current_track_index]

        try:
            mixer.music.load(str(file_path))
            mixer.music.play()
            self.is_playing = True
        except Exception as e:
            print(f"Error playing file: {e}")
            self.next_track()


    def update(self):
        """
        Этот метод должен вызываться регулярно в основном цикле приложения.
        Он проверяет очередь событий pygame и реагирует на окончание трека.
        """
        
        for evt in pg_event.get():
            if evt.type == TRACK_END_EVENT:
                self.message = "Its track end event"
                # Трек закончился, переключаем на следующий
                self.is_playing = False
                self.next_track()
                break # Обрабатываем только одно такое событие за раз


    def old_play_audio(self, file_path:Path) -> None:
        if not file_path.exists():
            print("File isn't exist")

        mixer.music.load(file_path)
        mixer.music.play()
        print(f"playing file - {file_path.name}")
