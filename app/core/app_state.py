#core/app_state.py
import json
from pathlib import Path

from pygame.mixer_music import play

DEFAULT_CONFIG = {
    "settings": {
        "root_path": "D:\\Audio",
        "supported_formats": [
            ".mp3", 
            ".ogg", 
            ".wav", 
            ".flac"
        ],
        "excluded_folders": [
            "D:\\Music\\Audio\\Подкасты",
            "D:\\Music\\Audio\\Звуки_системы",
            "D:\\Programs\\Projects\\Projects Python\\Flacify\\music\\secret",
            ".trash"
        ],
        "playlists_dir": ".\\playlists",
        "ui": {
            "theme": "dark",
            "accent_color": "#000000",
            "button_color": "#181818",
            "active_color": "#1DB954"
        }
    },
    "state": {
        "volume": 0.25,
        "current_library_path": "",
        "current_track_path": "",
        "current_track_index": 0
    },
    "library": {}
}


class AppState:
    """
    Centralized storage of application configuration and state.

    Loading: Once at startup (in MainFluentWindow).
    Writing to file: Only when explicitly calling save() (Save button or closing the application).
    """

    def __init__(self, config_path: str | Path = "config.json"):
        self._config_path = Path(config_path)
        self._data: dict = {}
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


    def _save(self) -> None:
        """
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
        ui_config = {self.ui_config}
        ------------------
         \t---- state ----
        volume = {self.volume}
        current_library_path = {self.current_library_path}
        current_track_path = {self.current_track_path}
        current_track_index = {self.current_track_index}
        playlist_paths = {[f'{str(x)}' for x in self.playlist_paths]}
        ------------------
         \t--- library ---
        library = {self.library}
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

    @property
    def playlists_dir(self) -> Path:
        return Path(self._data["settings"].get("playlists_dir", "."))

    @property
    def ui_config(self) -> dict:
        return self._data["settings"]["ui"]

    def update_ui_config(self, updates: dict) -> None:
        """Batch update of UI settings."""
        self._data["settings"]["ui"].update(updates)

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
            playlist = self._data["state"].get("playlist_paths", "")
            idx = self._data["state"].get("current_track_index", "")
            if playlist and idx:
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

    # ==================== library ====================

    @property
    def library(self) -> dict:
        return self._data["library"]

    def update_library(self, updates: dict) -> None:
        self._data["library"].update(updates)