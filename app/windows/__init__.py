# app/windows/__init__.py
from .home_window import HomeWindow
from .main_fluent_window import MainFluentWindow
from .playlist_detail_window import PlaylistDetailWindow
from .playlists_window import PlaylistsWindow
from .settings_window import SettingsWindow 

__all__ = [
    "HomeWindow",
    "MainFluentWindow",
    "PlaylistDetailWindow",
    "PlaylistsWindow",
    "SettingsWindow",
]