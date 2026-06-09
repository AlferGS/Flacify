import os
import json
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
from AudioPlayerController import AudioPlayerController


class FileBrowserModel(QObject):
    directoryChanged = pyqtSignal()
    playbackStarted = pyqtSignal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = self.__load_config()
        self.current_pos = self.root_path
        self.audio_player: AudioPlayerController | None = None


    def __load_config(self) -> dict:
        config_path = Path("config.json")
        if not config_path.exists():
            print("Config file not exist")
            raise FileNotFoundError("Config file not exist")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

        except Exception as e:
            print(f"Can't open config file {e}")
            raise Exception(e)            

        return config
    

    @property
    def root_path(self) -> Path:
        return Path(self.config.get("library", "").get("root_path", ""))


    @property
    def excluded_folders(self) -> list[Path]:
        if self.config:
            return list(map(lambda path: Path(path), self.config.get("library", "").get("excluded_folders", [])))
        else:
            return []


    @property
    def supported_formats(self) -> list[str]:
        return self.config.get("library", "").get("supported_formats", [])


    @property
    def current_dir(self) -> dict[int,Path]:
        current_dir = dict()
        index = 0

        for file in self.current_pos.iterdir():
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


    def open_folder(self, path:Path):
        """ Open folder end update directory in ui
        Args:
            path (Path): path to folder
        """
        self.current_pos = path
        self.directoryChanged.emit()    # Emit signal for HomeWindow to update ui

    
    def play_file(self, path:Path):
        """ Emit play for AudioPlayerController
        Args:
            path (Path): path to audio file
        """
        playlist = self.create_playlist_from_dir()
        if not playlist:
            print("No audio files in directory")
            return
        
        self.audio_player = AudioPlayerController(playlist) # Пересмотреть код, возможно хранить audioPlayer на уровне MainWindow

        # Находим индекс выбранного файла в плейлисте
        try:
            start_index = playlist.index(path)
            self.audio_player.current_track_index = start_index
            self.audio_player.play_current_track()
            self.playbackStarted.emit(path) # Emit signal 
        except ValueError:
            print("File not found in playlist")


    def open_file(self, index:int) -> None:
        #if index not in self.current_dir -> return
        assume_path = self.current_pos / self.current_dir[index]
        
        if assume_path.is_dir():
            self.current_pos = assume_path
            print(f"Entered directory: {assume_path.name}")
        elif assume_path.is_file():
            print(f"------------------------------------------{self.current_pos}")              # Добавить проверку на активный AudioPlayerController
            playlist = self.create_playlist_from_dir()
            self.audio_player = AudioPlayerController(playlist)
            # Находим индекс выбранного файла в плейлисте
            try:
                start_index = playlist.index(assume_path)
                self.audio_player.current_track_index = start_index
                self.audio_player.play_current_track()
            except ValueError:
                print("File not found in playlist")


    def next_song(self) -> None:
        if self.audio_player:
            self.audio_player.next_track()

    
    def prev_song(self) -> None:
        if self.audio_player:
            self.audio_player.prev_track()


    def update(self):
        if self.audio_player:
            self.audio_player.update()


    def back_previous_dir(self) -> None:
        if self.current_pos != self.root_path:
            self.current_pos = self.current_pos.parent
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
    print(f.current_dir)
    f.open_file(2)
    while True:
        inp = input("enter q to quit: ")
        if inp.upper() == 'Q':
            break