#core/file_browser_model.py
import json
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal

import app

from .audio_player_controller import AudioPlayerController
from .metadata_reader import MetadataReader
from .app_state import AppState


class FileBrowserModel(QObject):
    directoryChanged = pyqtSignal()
    playbackStarted = pyqtSignal(Path)

    def __init__(self, audio_player: AudioPlayerController, app_state: AppState, parent=None):
        super().__init__(parent)
        self.audio_player = audio_player
        self.app_state = app_state

        saved_path = self.app_state.current_library_path
        root = self.root_path
        
        if saved_path and Path(saved_path).exists() and Path(saved_path).is_relative_to(root):
            self.current_pos = Path(saved_path)
        else:
            self.current_pos = root
    

    @property
    def root_path(self) -> Path:
        return Path(self.app_state.root_path) if self.app_state.root_path else Path(".")


    @property
    def excluded_folders(self) -> list[Path]:
        return [Path(p) for p in self.app_state.excluded_folders]


    @property
    def supported_formats(self) -> list[str]:
        return self.app_state.supported_formats


    @property
    def current_dir(self) -> dict[int,Path]:
        current_dir = dict()
        index = 0

        dirs = []
        files_with_meta = []

        for item in self.current_pos.iterdir():
            if not self.is_supported(item):
                continue
                
            if item.is_dir():
                dirs.append(item)
            elif item.is_file():
                meta = MetadataReader.get_metadata(item)
                files_with_meta.append((item, meta.get('track', 0)))

        # Sorting folders by name
        dirs.sort(key=lambda p: p.name.lower())
        
        # Sorting files: by track number -> if 0, sort by name
        files_with_meta.sort(key=lambda x: (x[1] if x[1] > 0 else 9999, x[0].name.lower()))
        
        # Merge: folders upper, sorted files bottom
        sorted_items = dirs + [f[0] for f in files_with_meta]

        for file in sorted_items:
            if self.is_supported(file):
                current_dir[index] = file
                index += 1

        return current_dir


    def is_supported(self, file:Path) -> bool:
        if file.is_dir():
            if file in self.excluded_folders:
                return False
            if file.name.startswith("."):
                return False
            return True
        elif file.is_file():
            return file.suffix.lower() in self.supported_formats
        return False


    def handle_item_click(self, filename: str):
        full_path = self.current_pos / filename
        if full_path.is_dir():
            self.open_folder(full_path)
        elif full_path.is_file():
            self.play_file(full_path)


    def open_folder(self, path: Path):
        self.current_pos = path
        if self.app_state:
            self.app_state.current_library_path = str(path)
        self.directoryChanged.emit()

    
    def play_file(self, path:Path):
        """ Emit play for AudioPlayerController
        Args:
            path (Path): path to audio file
        """
        playlist = self.create_playlist_from_dir()
        if not playlist:
            print("No audio files in directory")
            return
        
        # self.audio_player = AudioPlayerController(playlist) # Пересмотреть код, возможно хранить audioPlayer на уровне MainWindow

        # Находим индекс выбранного файла в плейлисте
        try:
            start_index = playlist.index(path)
            self.audio_player.set_playlist(playlist, start_index)
            self.playbackStarted.emit(path) 
        except ValueError:
            print("File not found in playlist")


    def open_file(self, index:int) -> None:
        #if index not in self.current_dir -> return
        assume_path = self.current_pos / self.current_dir[index]
        
        if assume_path.is_dir():
            self.current_pos = assume_path
            self.directoryChanged.emit()
        elif assume_path.is_file():
            playlist = self.create_playlist_from_dir()
            # Находим индекс выбранного файла в плейлисте
            try:
                start_index = playlist.index(assume_path)
                self.audio_player.set_playlist(playlist, start_index)
            except ValueError:
                print("File not found in playlist")


    def next_song(self) -> None:
        if self.audio_player:
            self.audio_player.next_track()

    
    def prev_song(self) -> None:
        if self.audio_player:
            self.audio_player.prev_track()


    def back_previous_dir(self) -> None:
        if self.current_pos != self.root_path:
            self.current_pos = self.current_pos.parent
            self.app_state.current_library_path = self.current_pos
            self.directoryChanged.emit()
        else:
            print("You are in root directory")


    def print_config(self) -> None:
        print(self.config)
        

    def create_playlist_from_dir(self) -> list[Path]:
        current_dir = []
        for file in self.current_pos.iterdir():
            if file.is_file() and file.suffix.lower() in self.supported_formats:
                current_dir.append(file)

        return current_dir
    

if __name__ == "__main__":
    f = FileBrowserModel()
    f.open_file(2)
    while True:
        inp = input("enter q to quit: ")
        if inp.upper() == 'Q':
            break