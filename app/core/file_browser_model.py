#core/file_browser_model.py
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal

from .metadata_reader import MetadataReader
from .app_state import AppState


class FileBrowserModel(QObject):
    directoryChanged = pyqtSignal()
    directoryLoaded = pyqtSignal(list)
    playbackStarted = pyqtSignal(Path)
    nextTrack = pyqtSignal()
    prevTrack = pyqtSignal()
    

    def __init__(self, app_state: AppState, parent=None):
        """Init model and restore position from last session."""
        super().__init__(parent)
        self.app_state = app_state
        
        saved_path = self.app_state.current_library_path
        root = self.app_state.root_path
        if not saved_path.exists() or not saved_path.is_relative_to(root):
            self.app_state.current_library_path = root


    def __get_current_dir(self) -> list[Path]:
        """Returns a sorted list of files and folders in the current directory."""
        current_pos = self.app_state.current_library_path
        if not current_pos.exists() or not current_pos.is_dir():
            return []

        dirs = []
        files_with_meta = []

        for item in current_pos.iterdir():
            if not self.__is_supported(item):
                continue
            if item.is_dir():
                dirs.append(item)
            elif item.is_file():
                meta = MetadataReader.get_metadata(item)
                files_with_meta.append((item, meta.get('track', 0)))

        dirs.sort(key=lambda p: p.name.lower())
        files_with_meta.sort(key=lambda x: (x[1] if x[1] > 0 else 9999, x[0].name.lower()))

        return dirs + [f[0] for f in files_with_meta]


    def __is_supported(self, file: Path) -> bool:
        """Check that file format in app_state.supported_formats.
        Skip app_state.excluded_folders."""
        if file.is_dir():
            if file in self.app_state.excluded_folders:
                return False
            if file.name.startswith("."):
                return False
            return True
        elif file.is_file():
            return file.suffix.lower() in self.app_state.supported_formats
        return False
    

    def __open_folder(self, path: Path):
        """Change app_state.current_library_path and emit directoryChanged"""
        self.app_state.current_library_path = path
        self.directoryChanged.emit()
    

    def __create_playlist_from_dir(self) -> list[Path]:
        """Get supported songs in directory and return in format list[Path]."""
        files_with_meta = []
        for file in self.app_state.current_library_path.iterdir():
            if not self.__is_supported(file):
                continue
            elif file.is_file:
                meta = MetadataReader.get_metadata(file)
                files_with_meta.append((file, meta.get('track', 0)))
        files_with_meta.sort(key=lambda x: (x[1] if x[1] > 0 else 9999, x[0].name.lower()))
        return [f[0] for f in files_with_meta]
    

    def _load_directory(self) -> None:
        """Loads the current directory and emits a signal with a sorted list of files.
        Called when requested by the HomeWindow.
        """
        items = self.__get_current_dir()
        self.directoryLoaded.emit(items)

    
    def _handle_item_click(self, item_path: Path):
        """Handling a click on an element."""
        if item_path.is_dir():
            self.__open_folder(item_path)
        elif item_path.is_file():
            self._play_file(item_path)


    def _play_file(self, path: Path):
        """Create playlist from directory.
        Save current playlist, path to file and track path in app_state.
        Emit playbackStarted.
        """
        playlist = self.__create_playlist_from_dir()
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


    def _back_previous_dir(self) -> None:
        """Back to previous directory."""
        current = self.app_state.current_library_path
        root = self.app_state.root_path
        
        if current != root:
            self.app_state.current_library_path = current.parent
            self.directoryChanged.emit()
        else:
            print("You are in root directory")
        