#components/playlist_nav_item.py
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QFontMetrics, QPainter
from qfluentwidgets.components.navigation.navigation_widget import NavigationWidget

from app.core.playlist import Playlist
from app.components.playlist_badge import draw_badge

# Left inset of the badge in expanded mode (clear of the selection indicator).
NAV_BADGE_LEFT = 10
# Gap between badge and label.
NAV_LABEL_GAP = 10
# width <= badge_size * factor  =>  treat as compact (collapsed) panel.
NAV_COMPACT_FACTOR = 2.0


class PlaylistNavItem(NavigationWidget):
    """Navigation row for a playlist: badge + name.

    Inherits NavigationWidget because addWidget() requires it and connects
    onClick to the base 'clicked' signal. The base paintEvent draws the
    rounded background + hover/selected + left indicator, so this row stays
    visually consistent with Home/Settings across qfluentwidgets versions.
    We only overlay the badge and the (elided) label — the base class has no
    icon/label of its own, so there is nothing to suppress and no double paint.
    Compact mode is detected by width (the base compact API is version-dependent).
    """

    def __init__(self, playlist: Playlist, badge_size: int = 36, parent=None):
        super().__init__(parent)
        self._badge_size = badge_size
        # Populate our own attributes BEFORE anything can trigger a repaint.
        self._sync(playlist)
        # NOTE: do NOT call setIcon/setText — NavigationWidget has neither.
        # The base class handles mouse/clicked; we must NOT make it transparent.

    # ==================== Public ====================
    def update_playlist(self, playlist: Playlist) -> None:
        """Refresh name/color/initials in place (rename / recolor)."""
        self._sync(playlist)
        self.update()

    # ==================== Paint ====================
    def paintEvent(self, event):
        # 1) Base paints rounded background + hover/selected + left indicator.
        super().paintEvent(event)

        # 2) Overlay our badge + label.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        h = self.height()
        w = self.width()
        s = max(16, min(self._badge_size, h - 4))
        color = QColor(self._color)
        compact = w <= int(self._badge_size * NAV_COMPACT_FACTOR)
        selected = bool(getattr(self, "isSelected", False))

        if compact:
            x = (w - s) // 2
            y = (h - s) // 2
            draw_badge(painter, QRectF(x, y, s, s), color, self._initials)
        else:
            x = NAV_BADGE_LEFT
            y = (h - s) // 2
            draw_badge(painter, QRectF(x, y, s, s), color, self._initials)

            text_left = x + s + NAV_LABEL_GAP
            avail = max(0, w - text_left - NAV_BADGE_LEFT)
            fm = QFontMetrics(self.font())
            elided = fm.elidedText(self._name, Qt.ElideRight, avail)
            # Slightly dim non-selected text, like native nav items.
            pen = QColor(255, 255, 255) if selected else QColor(255, 255, 255, 210)
            painter.setPen(pen)
            painter.setFont(self.font())
            painter.drawText(
                QRectF(text_left, 0, avail, h),
                Qt.AlignVCenter | Qt.AlignLeft,
                elided,
            )

        painter.end()

    # ==================== Private ====================
    def _sync(self, playlist: Playlist) -> None:
        self._playlist_id = playlist.id
        self._name = playlist.name
        self._color = playlist.color
        self._initials = playlist.get_initials()
        self.setToolTip(playlist.name)