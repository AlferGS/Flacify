#core/app_state.py
import json
import os
import sys
from pathlib import Path

DEFAULT_CONFIG = {
    "settings": {
        "root_path": str(Path.home() / "Music"),
        "supported_formats": [
            ".mp3",
            ".ogg",
            ".wav",
            ".flac"
        ],
        "excluded_folders": []
    },
    "state": {
        "volume": 0.25,
        "current_library_path": "",
        "current_track_path": "",
        "current_track_index": 0
    },
    "playlists_dir": "playlists"
}


def _is_playlists_dir_usable(path: Path) -> bool:
    """
    Try to create directory and write/remove a small probe file.
    Returns True if the directory is usable for playlists storage.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".flacify_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _fallback_playlists_dir() -> Path:
    """
    User-specific fallback directory for playlists.
    Used when CWD-relative ./playlists is not writable.
    """
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if base:
            return Path(base) / "Flacify" / "playlists"
        return Path.home() / "AppData" / "Local" / "Flacify" / "playlists"

    return Path.home() / ".local" / "share" / "flacify" / "playlists"


class AppState:
    """
    Centralized storage of application configuration and state.

    Loading: Once at startup (in MainFluentWindow).
    Writing to file: Only when explicitly calling save() (Save button or closing the application).
    """

    def __init__(self, config_path: str | Path = "config.json"):
        self._config_path = Path(config_path)
        self._data: dict = {}
        self._resolved_playlists_dir: Path | None = None
        self.__load_config_file()


    def __load_config_file(self) -> None:
        """Loads the configuration file. Creates defaults for missing keys."""
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                print(f"[AppState] Config loaded from {self._config_path}")
            except (json.JSONDecodeError, Exception) as e:
                print(f"[AppState] Read error {self._config_path}: {e}")
                self._data = {}
        else:
            print(f"[AppState] Config not found, creating a default one")
            self._data = {}

        # Recursively add missing keys from DEFAULT_CONFIG
        self.__merge_defaults(self._data, DEFAULT_CONFIG)


    def __merge_defaults(self, target: dict, defaults: dict) -> None:
        """Recursively adds keys from defaults if they are not present in target."""
        for key, value in defaults.items():
            if key not in target:
                target[key] = value
            elif isinstance(value, dict) and isinstance(target.get(key), dict):
                self.__merge_defaults(target[key], value)


    def save(self) -> None:
        """Public API: persist current state to config.json."""
        self._save()

    def _save(self) -> None:
        """
        Internal implementation. Prefer save() from UI/external code.

        Explicitly writes the current state to a file.
        Called ONLY when the Save button is clicked or the application is closed.
        """
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            print(f"[AppState] The config is saved in {self._config_path}")
        except Exception as e:
            print(f"[AppState] Saving error: {e}")


    def print_app_state(self):
        print(f"""
        \t--- settings ---
        root_path = {self.root_path}
        supported_formats = {self.supported_formats}
        excluded_folders = {self.excluded_folders}
        playlists_dir = {self.playlists_dir}
        ------------------
         \t---- state ----
        volume = {self.volume}
        current_library_path = {self.current_library_path}
        current_track_path = {self.current_track_path}
        current_track_index = {self.current_track_index}
        playlist_paths = {[f'{str(x)}' for x in self.playlist_paths]}
        ------------------
        """)

    # ==================== settings ====================
    
    @property
    def root_path(self) -> Path:
        val = self._data["settings"].get("root_path", ".")
        return Path(val) if val else Path(".")

    @root_path.setter
    def root_path(self, value: Path | str) -> None:
        self._data["settings"]["root_path"] = str(value)

    @property
    def supported_formats(self) -> list[str]:
        return self._data["settings"]["supported_formats"]

    @property
    def excluded_folders(self) -> list[Path]:
        return [Path(p) for p in self._data["settings"].get("excluded_folders", [])]

    # ==================== state ====================

    @property
    def volume(self) -> float:
        return self._data["state"]["volume"]

    @volume.setter
    def volume(self, value: float) -> None:
        self._data["state"]["volume"] = max(0.0, min(1.0, float(value)))

    @property
    def current_library_path(self) -> Path:
        val = self._data["state"].get("current_library_path", "")
        return Path(val) if val else self.root_path

    @current_library_path.setter
    def current_library_path(self, value: Path | str) -> None:
        self._data["state"]["current_library_path"] = str(value)

    @property
    def current_track_path(self) -> Path:
        val = self._data["state"].get("current_track_path", "")
        if val == "":
            playlist = self._data["state"].get("playlist_paths", [])
            idx = self._data["state"].get("current_track_index", -1)
            if isinstance(idx, int) and 0 <= idx < len(playlist):
                val = playlist[idx]
        return Path(val) if val else Path("")

    @current_track_path.setter
    def current_track_path(self, value: Path | str) -> None:
        self._data["state"]["current_track_path"] = str(value)

    @property
    def current_track_index(self) -> int:
        return self._data["state"]["current_track_index"]

    @current_track_index.setter
    def current_track_index(self, value: int) -> None:
        self._data["state"]["current_track_index"] = int(value)

    @property
    def playlist_paths(self) -> list[Path]:
        """Returns a list of track paths of the last playlist.."""
        return [Path(p) for p in self._data["state"].get("playlist_paths", [])]

    @playlist_paths.setter
    def playlist_paths(self, paths: list[Path]) -> None:
        self._data["state"]["playlist_paths"] = [str(p) for p in paths]

    # ==================== playlists ==================

    @property
    def playlists_dir(self) -> Path:
        """
        Resolve playlists directory with CWD-first strategy and user-dir fallback.

        If config contains a relative path, e.g. "playlists":
          1. try ./playlists relative to current working directory;
          2. if not writable, fallback to user data directory;
          3. remember fallback in runtime config to avoid splitting playlists.

        Absolute paths are respected as-is.
        """
        if self._resolved_playlists_dir is not None:
            return self._resolved_playlists_dir

        raw = self._data.get("playlists_dir", "playlists")
        configured = Path(raw)

        if configured.is_absolute():
            chosen = configured
        else:
            cwd_candidate = Path.cwd() / configured
            fallback = _fallback_playlists_dir()

            if _is_playlists_dir_usable(cwd_candidate):
                chosen = cwd_candidate
            elif _is_playlists_dir_usable(fallback):
                print(
                    "[AppState] Playlists directory "
                    f"'{cwd_candidate}' is not writable. "
                    f"Using fallback: {fallback}"
                )
                chosen = fallback
                # Persist fallback for this process and future explicit saves.
                # This prevents creating a second playlist library after restart.
                self._data["playlists_dir"] = str(chosen)
            else:
                print(
                    "[AppState] Warning: neither "
                    f"'{cwd_candidate}' nor fallback '{fallback}' is writable. "
                    "Playlist saving may fail."
                )
                chosen = cwd_candidate

        self._resolved_playlists_dir = chosen
        return chosen
