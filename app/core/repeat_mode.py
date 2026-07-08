from enum import Enum, auto

class RepeatMode(Enum):
    OFF = auto()            # Off repeat
    ALBUM_LOOP = auto()     # Repeat playlist
    SONG_LOOP = auto()      # Repeat song

    def next(self) -> "RepeatMode":
        """Return next state: OFF -> ALBUM_LOOP -> SONG_LOOP -> OFF"""
        modes = list(RepeatMode)
        current_index = modes.index(self)
        return modes[(current_index + 1) % len(modes)]