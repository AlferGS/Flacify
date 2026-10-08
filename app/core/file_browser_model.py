#core/file_browser_model.py
import logging
from pathlib import Path

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from .metadata_reader import MetadataReader
from .app_state import AppState

logger = logging.getLogger("file_browser")


def _is_supported_entry(path: Path, app_state: AppState) -> bool:
    """Single source of truth for directory-entry filtering."""
    if path.is_dir():
        if path in app_state.excluded_folders:
            return False
        if path.name.startswith("."):
            return False
        return True
    if path.is_file():
        return path.suffix.lower() in app_state.supported_formats
    return False


def _scan_directory_entries(
    current_path: Path,
    app_state: AppState,
    get_meta,
    should_cancel=None,
):
    """Shared scan used by the worker (background) and the model (cache-only).

    Returns:
        (dirs, files) on success.
        (None, None) if cancelled.

    files is list[(Path, meta)] ordered by (track>0 else 9999, name.lower()).
    get_meta(path)->dict decides the metadata source:
      - worker passes MetadataReader.get_metadata (IO is fine off the UI thread);
      - model passes a cache-only lookup (no IO).
    """
    dirs: list[Path] = []
    files: list[tuple[Path, dict]] = []

    try:
        iterator = current_path.iterdir()
    except OSError as exc:
        logger.warning("Cannot iterate directory %s: %s", current_path, exc)
        return [], []

    for index, item in enumerate(iterator):
        if should_cancel is not None and (index & 31) == 0 and should_cancel():
            logger.info("Directory scan cancelled: %s", current_path)
            return None, None

        if not _is_supported_entry(item, app_state):
            continue

        if item.is_dir():
            dirs.append(item)
        elif item.is_file():
            files.append((item, get_meta(item)))

    dirs.sort(key=lambda p: p.name.lower())
    files.sort(key=lambda x: (
        x[1].get("track", 0) if x[1].get("track", 0) > 0 else 9999,
        x[0].name.lower(),
    ))

    return dirs, files


class DirectoryScanWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, current_path: Path, app_state: AppState):
        super().__init__()
        self.current_path = current_path
        self.app_state = app_state

    def __should_cancel(self) -> bool:
        try:
            thread = self.thread()
            return bool(thread is not None and thread.isInterruptionRequested())
        except RuntimeError:
            return False

    def __build_payload(self) -> dict | None:
        current_pos = self.current_path

        if not current_pos.exists() or not current_pos.is_dir():
            return {
                "path": current_pos,
                "dirs": [],
                "items": [],
                "playlist": [],
                "metadata": {},
            }

        dirs, files = _scan_directory_entries(
            current_pos,
            self.app_state,
            MetadataReader.get_metadata,
            self.__should_cancel,
        )

        if dirs is None:
            return None

        metadata_map = {p: m for p, m in files}
        file_paths = [p for p, _ in files]
        items = dirs + file_paths

        return {
            "path": current_pos,
            "dirs": dirs,
            "items": items,
            "playlist": file_paths,
            "metadata": metadata_map,
        }

    @pyqtSlot()
    def run(self) -> None:
        try:
            payload = self.__build_payload()
            self.finished.emit(payload)
        except Exception as exc:
            logger.exception("Directory scan worker failed: %s", self.current_path)
            self.error.emit(str(exc))


class FileBrowserModel(QObject):
    directoryChanged = pyqtSignal()
    directoryLoaded = pyqtSignal(object)
    playbackStarted = pyqtSignal(Path)

    def __init__(self, app_state: AppState, parent=None):
        """Init model and restore position from last session."""
        super().__init__(parent)
        self.app_state = app_state
        self._metadata_cache: dict[Path, dict] = {}
        self._scan_generation = 0
        self._active_thread: QThread | None = None
        self._active_worker: DirectoryScanWorker | None = None

        # Latest successful scan state. Used to avoid filesystem IO in UI thread
        # when clicking folders/tracks or starting playback from directory.
        self._current_scan_dir: Path | None = None
        self._current_scan_dirs: set[Path] = set()
        self._current_scan_files: set[Path] = set()
        self._current_scan_playlist: list[Path] | None = None

        saved_path = self.app_state.current_library_path
        root = self.app_state.root_path
        if not saved_path.exists() or not saved_path.is_relative_to(root):
            self.app_state.current_library_path = root

    def __open_folder(self, path: Path):
        """Change app_state.current_library_path and emit directoryChanged."""
        self.app_state.current_library_path = path
        self.directoryChanged.emit()

    def _meta_from_cache(self, path: Path) -> dict:
        """Cache-only metadata lookup; never does IO on the UI thread.

        Miss => {"track": 0} (sort by name). In the normal flow the cache is
        warm, because the worker scanned this exact directory before the rows
        were rendered, so a click can only happen after a successful scan.
        """
        return self._metadata_cache.get(path) or {"track": 0}

    def __create_playlist_from_dir(self) -> list[Path]:
        """Build a playback order from the current directory using cached metadata."""
        current_path = self.app_state.current_library_path
        if not current_path.exists() or not current_path.is_dir():
            return []

        _, files = _scan_directory_entries(
            current_path,
            self.app_state,
            self._meta_from_cache,
        )

        if files is None:
            return []

        return [p for p, _ in files]

    def _interrupt_active_scan(self) -> None:
        """Safely request interruption of the previous directory scan.

        QThread may already be deleted via deleteLater(), while the Python
        attribute still points to the dangling wrapper. Calling methods on it
        raises RuntimeError, so treat deleted threads as finished and drop refs.
        """
        thread = self._active_thread
        if thread is None:
            return

        try:
            if thread.isRunning():
                thread.requestInterruption()
        except RuntimeError:
            # Wrapped C++ object has been deleted; this is a stale reference.
            pass
        finally:
            if self._active_thread is thread:
                self._active_thread = None
                self._active_worker = None

    def _load_directory(self) -> None:
        """Load the current directory asynchronously and emit a scan payload."""
        self._scan_generation += 1
        generation = self._scan_generation
        current_path = self.app_state.current_library_path

        logger.info("Scan requested: generation=%s path=%s", generation, current_path)

        # Ask the previous scan to stop as soon as its cooperative checkpoint is reached.
        self._interrupt_active_scan()

        if not current_path.exists() or not current_path.is_dir():
            self._current_scan_dir = current_path
            self._current_scan_dirs = set()
            self._current_scan_files = set()
            self._current_scan_playlist = []

            self.directoryLoaded.emit({
                "path": current_path,
                "dirs": [],
                "items": [],
                "playlist": [],
                "metadata": {},
            })
            return

        thread = QThread(self)
        worker = DirectoryScanWorker(current_path, self.app_state)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(
            lambda payload, gen=generation: self._on_directory_scan_finished(payload, gen)
        )
        worker.error.connect(
            lambda message, gen=generation: self._on_directory_scan_error(message, gen)
        )

        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._active_thread = thread
        self._active_worker = worker
        thread.start()

    def _on_directory_scan_finished(self, payload: object, generation: int) -> None:
        if payload is None:
            logger.info("Scan cancelled: generation=%s", generation)
            return

        if generation != self._scan_generation:
            logger.info("Scan result ignored as stale: generation=%s", generation)
            return

        payload = payload or {}

        self._current_scan_dir = payload.get("path")
        self._current_scan_dirs = set(payload.get("dirs", []))
        self._current_scan_files = set(payload.get("playlist", []))
        self._current_scan_playlist = list(payload.get("playlist", []))

        metadata = payload.get("metadata", {})
        self._metadata_cache.update(metadata)

        logger.info(
            "Scan finished: generation=%s path=%s dirs=%s files=%s",
            generation,
            self._current_scan_dir,
            len(self._current_scan_dirs),
            len(self._current_scan_files),
        )

        self.directoryLoaded.emit(payload)

    def _on_directory_scan_error(self, message: str, generation: int) -> None:
        if generation != self._scan_generation:
            return

        # Do not emit an empty payload: a transient scan error should not wipe the current list.
        logger.error("Directory scan error: generation=%s message=%s", generation, message)

    # ==================== Public API ====================
    def handle_item_click(self, item_path: Path) -> None:
        """Public API: handle click on browser item."""
        self._handle_item_click(item_path)

    def load_directory(self) -> None:
        """Public API: start asynchronous scan of current library directory."""
        self._load_directory()

    def back_previous_dir(self) -> None:
        """Public API: go to parent directory."""
        self._back_previous_dir()

    def _handle_item_click(self, item_path: Path):
        """Handling a click on an element without extra filesystem stat when possible."""
        if item_path in self._current_scan_dirs:
            self.__open_folder(item_path)
            return

        if item_path in self._current_scan_files:
            self._play_file(item_path)
            return

        # Fallback for stale/unknown entries.
        if item_path.is_dir():
            self.__open_folder(item_path)
        elif item_path.is_file():
            self._play_file(item_path)

    def _play_file(self, path: Path):
        """Start playback using the playlist from the latest scan when possible."""
        current_dir = self.app_state.current_library_path

        if (
            self._current_scan_dir == current_dir
            and self._current_scan_playlist is not None
        ):
            playlist = list(self._current_scan_playlist)
        else:
            playlist = self.__create_playlist_from_dir()

        if not playlist:
            logger.info("No audio files in directory: %s", current_dir)
            return

        try:
            self.app_state.playlist_paths = playlist
            self.app_state.current_track_index = playlist.index(path)
            self.app_state.current_track_path = path
            self.playbackStarted.emit(path)
        except ValueError:
            logger.warning("File not found in directory playlist: %s", path)

    def _back_previous_dir(self) -> None:
        """Back to previous directory."""
        current = self.app_state.current_library_path
        root = self.app_state.root_path

        if current != root:
            self.app_state.current_library_path = current.parent
            self.directoryChanged.emit()
        else:
            print("You are in root directory")