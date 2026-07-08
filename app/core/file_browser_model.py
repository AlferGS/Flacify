#core/file_browser_model.py
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal
from pygame.mixer_music import play
from pygame.sprite import LayeredDirty

from .metadata_reader import MetadataReader
from .app_state import AppState


class FileBrowserModel(QObject):
    directoryChanged = pyqtSignal()
    directoryLoaded = pyqtSignal(list)
    playbackStarted = pyqtSignal(Path)
    nextTrack = pyqtSignal()
    prevTrack = pyqtSignal()
    

    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        
        saved_path = self.app_state.current_library_path
        root = self.app_state.root_path
        if not saved_path.exists() or not saved_path.is_relative_to(root):
            self.app_state.current_library_path = root


    def load_directory(self) -> None:
        """
        Загружает текущую директорию и эмитит сигнал с отсортированным списком файлов.
        Вызывается при запросе от HomeWindow.
        """
        items = self.get_current_dir()
        self.directoryLoaded.emit(items)


    def get_current_dir(self) -> list[Path]:
        """Возвращает отсортированный список файлов и папок в текущей директории."""
        current_pos = self.app_state.current_library_path
        if not current_pos.exists() or not current_pos.is_dir():
            return []

        dirs = []
        files_with_meta = []

        for item in current_pos.iterdir():
            if not self.is_supported(item):
                continue
            if item.is_dir():
                dirs.append(item)
            elif item.is_file():
                meta = MetadataReader.get_metadata(item)
                files_with_meta.append((item, meta.get('track', 0)))

        dirs.sort(key=lambda p: p.name.lower())
        files_with_meta.sort(key=lambda x: (x[1] if x[1] > 0 else 9999, x[0].name.lower()))

        return dirs + [f[0] for f in files_with_meta]


    def is_supported(self, file: Path) -> bool:
        if file.is_dir():
            if file in self.app_state.excluded_folders:
                return False
            if file.name.startswith("."):
                return False
            return True
        elif file.is_file():
            return file.suffix.lower() in self.app_state.supported_formats
        return False
    
    
    def handle_item_click(self, item_path: Path):
        """Обработка клика по элементу"""
        if item_path.is_dir():
            self.open_folder(item_path)
        elif item_path.is_file():
            self.play_file(item_path)

    
    def open_folder(self, path: Path):
        self.app_state.current_library_path = path
        self.directoryChanged.emit()


    def play_file(self, path: Path):
        playlist = self.create_playlist_from_dir()
        if not playlist:
            print("No audio files in directory")
            return
        try:
            self.app_state.playlist_paths = playlist
            self.app_state.current_track_index = playlist.index(path)
            self.app_state.current_track_path = path
            self.playbackStarted.emit(path) 
        except ValueError:
            print("File not found in playlist")


    def back_previous_dir(self) -> None:
        current = self.app_state.current_library_path
        root = self.app_state.root_path
        
        if current != root:
            self.app_state.current_library_path = current.parent
            self.directoryChanged.emit()
        else:
            print("You are in root directory")


    def print_config(self) -> None:
        print(self.config)
        
    
    def create_playlist_from_dir(self) -> list[Path]:
        files_with_meta = []
        for file in self.app_state.current_library_path.iterdir():
            if not self.is_supported(file):
                continue
            elif file.is_file:
                meta = MetadataReader.get_metadata(file)
                files_with_meta.append((file, meta.get('track', 0)))
        files_with_meta.sort(key=lambda x: (x[1] if x[1] > 0 else 9999, x[0].name.lower()))
        return [f[0] for f in files_with_meta]

