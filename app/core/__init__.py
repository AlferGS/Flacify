# app/components/__init__.py

from .audio_player_controller import AudioPlayerController
from .file_browser_model import FileBrowserModel
from .metadata_reader import MetadataReader

# Опционально: ограничиваем импорт по "звездочке"
__all__ = [
    "AudioPlayerController",
    "FileBrowserModel", 
    "MetadataReader",
]