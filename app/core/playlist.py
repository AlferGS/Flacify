#core/playlist.py
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

@dataclass
class PlaylistTrack:
    # Single Track in playlist
    path: Path
    added_at: datetime

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "added_at": self.added_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> PlaylistTrack:
        return cls(
            path=Path(data["path"]),
            added_at=datetime.fromisoformat(data["added_at"]),
        )


@dataclass
class Playlist:
    """Playlist: name, color, sorted track list."""

    id: str
    name: str
    color: str  # HEX
    created_at: datetime
    updated_at: datetime
    tracks: list[PlaylistTrack] = field(default_factory=list)

    def add_track(self, path: Path, index: Optional[int] = None) -> None:
        """Add track to the end of playlist."""
        entry = PlaylistTrack(path=path, added_at=datetime.now())
        if index is None or index >= len(self.tracks):
            self.tracks.append(entry)
        else:
            self.tracks.insert(index, entry)
        self.updated_at = datetime.now()

    def remove_track_at(self, index: int) -> None:
        """Remove track from playlist by index."""
        if 0 <= index < len(self.tracks):
            self.tracks.pop(index)
            self.updated_at = datetime.now()

    def move_track(self, from_idx: int, to_idx: int) -> None:
        """Move track position in playlist (drag&drop)."""
        if from_idx == to_idx:
            return
        if 0 <= from_idx < len(self.tracks) and 0 <= to_idx < len(self.tracks):
            entry = self.tracks.pop(from_idx)
            self.tracks.insert(to_idx, entry)
            self.updated_at = datetime.now()

    # Requests

    def contains(self, path: Path) -> bool:
        return any(t.path == path for t in self.tracks)

    def get_initials(self) -> str:
        """Get initials of playlist name and return it .UPPER()."""
        words = self.name.split()
        initials = "".join(w[0] for w in words if w)
        return initials[:4].upper()

    @property
    def track_paths(self) -> list[Path]:
        """Return track pathes in list format for player."""
        return [t.path for t in self.tracks]

    # Serialization

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tracks": [t.to_dict() for t in self.tracks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Playlist:
        return cls(
            id=data["id"],
            name=data["name"],
            color=data.get("color", "#1DB954"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            tracks=[PlaylistTrack.from_dict(t) for t in data.get("tracks", [])],
        )

    def save(self, directory: Path) -> None:
        """Save playlist by <id>.json in file directory."""
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{self.id}.json"
        file_path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, file_path: Path) -> Optional[Playlist]:
        """Load playlist from JSON-file. Return None when error."""
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    # Factory

    @classmethod
    def create(cls, name: str, color: str) -> Playlist:
        """СCreate new playlist with generating unique id."""
        now = datetime.now()
        return cls(
            id=uuid.uuid4().hex[:8],
            name=name,
            color=color,
            created_at=now,
            updated_at=now,
            tracks=[],
        )