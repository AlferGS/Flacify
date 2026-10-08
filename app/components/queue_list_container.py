#components/queue_list_container.py
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

from .queue_track_item import QueueTrackItem


class BaseTrackListContainer(QWidget):
    """Shared vertical list of draggable track rows with reordering.

    Owns the drag machine (start/move/finish), the item list and the layout.
    Emits order_changed(from_index, to_index) — position-based, duplicate-safe.
    Subclasses provide row widgets (via set_items) and any extra signals.
    """
    order_changed = pyqtSignal(int, int)  # (from_index, to_index)

    def __init__(self, spacing: int = 4, margins=(4, 4, 4, 4), parent=None):
        super().__init__(parent)
        self._items: list = []
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(*margins)
        self._layout.setSpacing(spacing)
        self._drag_item = None
        self._drag_start_index = -1

    # ==================== Public ====================
    def set_items(self, items: list) -> None:
        """Replace all rows with the given widgets (old ones are deleted)."""
        self._dispose_items()
        self._items = list(items)
        for item in self._items:
            self._connect_drag(item)
            self._layout.addWidget(item)
        self._layout.addStretch(1)

    def items(self) -> list:
        """Current row widgets in display order."""
        return list(self._items)

    # ==================== Drag machine (shared) ====================
    def _connect_drag(self, item) -> None:
        item.drag_started.connect(self._on_drag_started)
        item.drag_moved.connect(self._on_drag_moved)
        item.drag_finished.connect(self._on_drag_finished)

    def _on_drag_started(self, item) -> None:
        self._drag_item = item
        self._drag_start_index = self._items.index(item) if item in self._items else -1

    def _on_drag_moved(self, item, global_pos) -> None:
        if self._drag_item is None:
            return
        cursor_y = self.mapFromGlobal(global_pos).y()
        target = self._item_at_y(cursor_y)
        if target is None or target is self._drag_item:
            return
        rect = target.geometry()
        mid_y = rect.top() + rect.height() // 2
        from_index = self._items.index(self._drag_item)
        to_index = self._items.index(target)
        if (cursor_y < mid_y and from_index > to_index) or \
           (cursor_y > mid_y and from_index < to_index):
            self._items.pop(from_index)
            self._items.insert(to_index, self._drag_item)
            self._rebuild()

    def _on_drag_finished(self, item) -> None:
        if self._drag_item is None:
            return
        new_index = self._items.index(self._drag_item)
        if self._drag_start_index != -1 and new_index != self._drag_start_index:
            self.order_changed.emit(self._drag_start_index, new_index)
        self._drag_item = None
        self._drag_start_index = -1

    # ==================== Layout helpers ====================
    def _item_at_y(self, y: int):
        """Return item under cursor, tolerating spacing gaps."""
        if not self._items:
            return None

        spacing = max(0, self._layout.spacing())
        pad = spacing // 2 + 1

        for item in self._items:
            geo = item.geometry()
            if geo.top() - pad <= y <= geo.bottom() + pad:
                return item

        # Fallback: nearest item by midpoint.
        nearest = None
        nearest_dist = None
        for item in self._items:
            geo = item.geometry()
            mid = geo.top() + geo.height() // 2
            dist = abs(y - mid)
            if nearest_dist is None or dist < nearest_dist:
                nearest = item
                nearest_dist = dist

        return nearest

    def _rebuild(self) -> None:
        """Reorder widgets without reparenting them.

        Important: setParent(None) during drag can drop Qt's implicit mouse grab.
        Then the dragged widget stops receiving mouseMoveEvent, and reorder
        appears to work only by one position.
        """
        for widget in self._items:
            if self._layout.indexOf(widget) != -1:
                self._layout.removeWidget(widget)

        # Remove remaining layout items, e.g. stretch.
        while self._layout.count():
            self._layout.takeAt(0)

        for widget in self._items:
            self._layout.addWidget(widget)

        self._layout.addStretch(1)
        self._layout.invalidate()
        self._layout.activate()

    def _dispose_items(self) -> None:
        """Detach and schedule deletion of all current rows (full replacement)."""
        while self._layout.count():
            child = self._layout.takeAt(0)
            w = child.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()


class QueueListContainer(BaseTrackListContainer):
    """Queue list: builds QueueTrackItem rows from paths, highlights by index."""
    track_double_clicked = pyqtSignal(int)  # clicked row index

    def __init__(self, parent=None):
        super().__init__(spacing=4, margins=(4, 4, 4, 4), parent=parent)
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(200)

    # ==================== Public ====================
    def _set_tracks(self, tracks: list[Path], current_index: int) -> None:
        """Clears and refills the track list from paths."""
        items = []
        for i, track in enumerate(tracks):
            item = QueueTrackItem(track, i == current_index)
            item.track_double_clicked.connect(self._on_track_double_clicked)
            items.append(item)
        self.set_items(items)

    def _update_current_highlight(self, current_index: int) -> None:
        """Update current highlight by queue index (duplicate-safe)."""
        for i, item in enumerate(self._items):
            old_is_current = item.is_current
            item.is_current = (i == current_index)
            if old_is_current != item.is_current:
                item._update_text_colors()
                item.update()

    # ==================== Protected ====================
    def _on_track_double_clicked(self, widget) -> None:
        """Translate clicked widget to its row index."""
        if widget in self._items:
            self.track_double_clicked.emit(self._items.index(widget))