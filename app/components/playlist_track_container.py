#components/playlist_track_container.py
from .queue_list_container import BaseTrackListContainer


class PlaylistTrackContainer(BaseTrackListContainer):
    """Playlist track rows with drag&drop reordering.

    Rows (SongListItem with drag_enabled=True) are built and wired by
    HomeWindow and handed to set_items(); this class only supplies the
    playlist-specific spacing/margins. order_changed(from,to) is inherited.
    """

    def __init__(self, parent=None):
        super().__init__(spacing=8, margins=(0, 0, 0, 0), parent=parent)