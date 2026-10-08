#core/playlist_manager.py
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

from app.core.playlist import Playlist


class PlaylistManager(QObject):
    playlists_changed = pyqtSignal()
    # Current playlist was updated (tracks, order)
    playlist_updated = pyqtSignal(str)  # playlist_id

    def __init__(self, playlists_dir: Path, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._playlists_dir = playlists_dir
        self._playlists: dict[str, Playlist] = {}
        self._ensure_directory()
        self._scan_directory()

    # Public properties

    @property
    def playlists_dir(self) -> Path:
        return self._playlists_dir

    # CRUD of playlists

    def create_playlist(self, name: str, color: str) -> str:
        """Create playlist, save it in directory, return id."""
        playlist = Playlist.create(name=name, color=color)
        self._playlists[playlist.id] = playlist

        try:
            playlist.save(self._playlists_dir)
        except OSError as e:
            print(f"[PlaylistManager] Cannot save new playlist {playlist.id}: {e}")

        self.playlists_changed.emit()
        return playlist.id

    def delete_playlist(self, playlist_id: str) -> None:
        """Delete playlist and his JSON-file."""
        if playlist_id not in self._playlists:
            return

        del self._playlists[playlist_id]

        file_path = self._playlists_dir / f"{playlist_id}.json"
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError as e:
            print(f"[PlaylistManager] Cannot delete playlist file {file_path}: {e}")

        self.playlists_changed.emit()

    def rename_playlist(self, playlist_id: str, new_name: str, new_color: str) -> None:
        """Rename playlist and/or change color."""
        playlist = self._playlists.get(playlist_id)
        if playlist is None:
            return
        playlist.name = new_name
        playlist.color = new_color
        self._save_playlist(playlist)

    # Track methods

    def add_tracks_to_playlists(self, paths: list[Path], playlist_ids: list[str]) -> None:
        """Add tracks in one or few playlists."""
        for pid in playlist_ids:
            playlist = self._playlists.get(pid)
            if playlist is None:
                continue
            for path in paths:
                playlist.add_track(path)
            self._save_playlist(playlist)

    def add_tracks_to_playlist(self, playlist_id: str, paths: list[Path]) -> None:
        """Add track ro one playlist."""
        self.add_tracks_to_playlists(paths, [playlist_id])

    def remove_track_from_playlist(self, playlist_id: str, track_index: int) -> None:
        """Delete track from playlist by index."""
        playlist = self._playlists.get(playlist_id)
        if playlist is None:
            return
        playlist.remove_track_at(track_index)
        self._save_playlist(playlist)

    def move_track_in_playlist(self, playlist_id: str, from_idx: int, to_idx: int) -> None:
        """Move track in playlist (drag&drop)."""
        playlist = self._playlists.get(playlist_id)
        if playlist is None:
            return
        playlist.move_track(from_idx, to_idx)
        self._save_playlist(playlist)

    # Requests
    def get_all_playlists(self) -> list[Playlist]:
        """Return playlists sorted by name (case-insensitive), then creation time."""
        return sorted(
            self._playlists.values(),
            key=lambda p: (p.name.lower(), p.created_at),
        )

    def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        return self._playlists.get(playlist_id)

    def get_playlists_containing_track(self, path: Path) -> list[Playlist]:
        """Return list of playlists containing track."""
        return [p for p in self._playlists.values() if p.contains(path)]

    # Protected
    def _ensure_directory(self) -> None:
        """Create folder playlists/ if it doesn't exist."""
        try:
            self._playlists_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(
                f"[PlaylistManager] Cannot create playlists directory "
                f"{self._playlists_dir}: {e}"
            )

    def _scan_directory(self) -> None:
        """Load all .json from playlists/ directory."""
        self._playlists.clear()
        if not self._playlists_dir.is_dir():
            return
        for file_path in sorted(self._playlists_dir.glob("*.json")):
            playlist = Playlist.load(file_path)
            if playlist is not None:
                self._playlists[playlist.id] = playlist

    def _save_playlist(self, playlist: Playlist) -> None:
        """Save playlist and emit signal."""
        try:
            playlist.save(self._playlists_dir)
        except OSError as e:
            print(f"[PlaylistManager] Cannot save playlist {playlist.id}: {e}")
            return

        self.playlist_updated.emit(playlist.id)