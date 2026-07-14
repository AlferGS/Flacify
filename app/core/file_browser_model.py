#core/file_browser_model.py
from pathlib import Path

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from .metadata_reader import MetadataReader
from .app_state import AppState


class DirectoryScanWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, current_path: Path, app_state: AppState):
        super().__init__()
        self.current_path = current_path
        self.app_state = app_state

    def __build_payload(self) -> dict:
        current_pos = self.current_path
        if not current_pos.exists() or not current_pos.is_dir():
            return {"items": [], "playlist": [], "metadata": {}}

        dirs: list[Path] = []
        files_with_meta: list[tuple[Path, int]] = []
        metadata_map: dict[Path, dict] = {}

        for item in current_pos.iterdir():
            if not self._is_supported(item):
                continue
            if item.is_dir():
                dirs.append(item)
            elif item.is_file():
                meta = MetadataReader.get_metadata(item)
                metadata_map[item] = meta
                files_with_meta.append((item, meta.get("track", 0)))

        dirs.sort(key=lambda p: p.name.lower())
        files_with_meta.sort(key=lambda x: (x[1] if x[1] > 0 else 9999, x[0].name.lower()))

        items = dirs + [item for item, _ in files_with_meta]
        playlist = [item for item, _ in files_with_meta]
        return {"items": items, "playlist": playlist, "metadata": metadata_map}

    @pyqtSlot()
    def run(self) -> None:
        try:
            payload = self.__build_payload()
            self.finished.emit(payload)
        except Exception as exc:
            self.error.emit(str(exc))

    def _is_supported(self, file: Path) -> bool:
        if file.is_dir():
            if file in self.app_state.excluded_folders:
                return False
            if file.name.startswith("."):
                return False
            return True
        if file.is_file():
            return file.suffix.lower() in self.app_state.supported_formats
        return False


class FileBrowserModel(QObject):
    directoryChanged = pyqtSignal()
    directoryLoaded = pyqtSignal(object)
    playbackStarted = pyqtSignal(Path)
    nextTrack = pyqtSignal()
    prevTrack = pyqtSignal()

    def __init__(self, app_state: AppState, parent=None):
        """Init model and restore position from last session."""
        super().__init__(parent)
        self.app_state = app_state
        self._metadata_cache: dict[Path, dict] = {}
        self._scan_generation = 0
        self._active_thread: QThread | None = None
        self._active_worker: DirectoryScanWorker | None = None

        saved_path = self.app_state.current_library_path
        root = self.app_state.root_path
        if not saved_path.exists() or not saved_path.is_relative_to(root):
            self.app_state.current_library_path = root

    def __open_folder(self, path: Path):
        """Change app_state.current_library_path and emit directoryChanged."""
        self.app_state.current_library_path = path
        self.directoryChanged.emit()

    def __create_playlist_from_dir(self) -> list[Path]:
        """Build a playlist from the current directory using the cached metadata."""
        current_path = self.app_state.current_library_path
        if not current_path.exists() or not current_path.is_dir():
            return []

        files_with_meta: list[tuple[Path, int]] = []
        for file in current_path.iterdir():
            if not self._is_supported(file):
                continue
            if file.is_file():
                meta = self._metadata_cache.get(file) or MetadataReader.get_metadata(file)
                if file not in self._metadata_cache:
                    self._metadata_cache[file] = meta
                files_with_meta.append((file, meta.get("track", 0)))

        files_with_meta.sort(key=lambda x: (x[1] if x[1] > 0 else 9999, x[0].name.lower()))
        return [item for item, _ in files_with_meta]

    def _load_directory(self) -> None:
        """Load the current directory asynchronously and emit a scan payload."""
        self._scan_generation += 1
        generation = self._scan_generation
        current_path = self.app_state.current_library_path

        if not current_path.exists() or not current_path.is_dir():
            self.directoryLoaded.emit({"items": [], "playlist": [], "metadata": {}})
            return

        thread = QThread(self)
        worker = DirectoryScanWorker(current_path, self.app_state)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(lambda payload, gen=generation: self._on_directory_scan_finished(payload, gen))
        worker.error.connect(lambda message, gen=generation: self._on_directory_scan_error(message, gen))
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._active_thread = thread
        self._active_worker = worker
        thread.start()

    def _on_directory_scan_finished(self, payload: dict, generation: int) -> None:
        if generation != self._scan_generation:
            return

        metadata = payload.get("metadata", {})
        self._metadata_cache.update(metadata)
        self.app_state.playlist_paths = payload.get("playlist", [])
        self.directoryLoaded.emit(payload)

    def _on_directory_scan_error(self, message: str, generation: int) -> None:
        if generation != self._scan_generation:
            return
        print(f"[FileBrowserModel] Directory scan error: {message}")
        self.directoryLoaded.emit({"items": [], "playlist": [], "metadata": {}})

    def _handle_item_click(self, item_path: Path):
        """Handling a click on an element."""
        if item_path.is_dir():
            self.__open_folder(item_path)
        elif item_path.is_file():
            self._play_file(item_path)

    def _play_file(self, path: Path):
        """Use the current directory playlist if available, otherwise build one."""
        playlist = self.app_state.playlist_paths
        if not playlist:
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

    def _is_supported(self, file: Path) -> bool:
        if file.is_dir():
            if file in self.app_state.excluded_folders:
                return False
            if file.name.startswith("."):
                return False
            return True
        if file.is_file():
            return file.suffix.lower() in self.app_state.supported_formats
        return False

    def _back_previous_dir(self) -> None:
        """Back to previous directory."""
        current = self.app_state.current_library_path
        root = self.app_state.root_path

        if current != root:
            self.app_state.current_library_path = current.parent
            self.directoryChanged.emit()
        else:
            print("You are in root directory")
        