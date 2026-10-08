#components/playlist_track_container.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget


class PlaylistTrackContainer(QWidget):
    """Container for playlist track rows with drag&drop reordering.
    Emits order_changed(from_index, to_index) once a drag completes."""
    order_changed = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: list = []
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self._drag_item = None
        self._drag_start_index = -1

    # ==================== Public ====================
    def set_items(self, items: list) -> None:
        """Fill the container with rows and wire their drag signals."""
        self.__clear_layout()
        self.items = list(items)
        for item in self.items:
            self.__connect_item(item)
            self.layout.addWidget(item)
        self.layout.addStretch(1)

    # ==================== Protected ====================
    def __clear_layout(self) -> None:
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def __connect_item(self, item) -> None:
        item.drag_started.connect(self.__on_drag_started)
        item.drag_moved.connect(self.__on_drag_moved)
        item.drag_finished.connect(self.__on_drag_finished)

    def __on_drag_started(self, item) -> None:
        self._drag_item = item
        self._drag_start_index = self.items.index(item) if item in self.items else -1

    def __on_drag_moved(self, item, global_pos) -> None:
        if self._drag_item is None:
            return
        cursor_y = self.mapFromGlobal(global_pos).y()
        target = self.__track_at_position(cursor_y)
        if target is None or target is self._drag_item:
            return
        target_rect = target.geometry()
        mid_y = target_rect.top() + target_rect.height() // 2
        from_index = self.items.index(self._drag_item)
        to_index = self.items.index(target)
        if (cursor_y < mid_y and from_index > to_index) or \
           (cursor_y > mid_y and from_index < to_index):
            self.items.pop(from_index)
            self.items.insert(to_index, self._drag_item)
            self.__rebuild()

    def __on_drag_finished(self, item) -> None:
        if self._drag_item is None:
            return
        new_index = self.items.index(self._drag_item)
        if self._drag_start_index != -1 and new_index != self._drag_start_index:
            self.order_changed.emit(self._drag_start_index, new_index)
        self._drag_item = None
        self._drag_start_index = -1

    def __rebuild(self) -> None:
        """Re-add rows in current items order (widgets are NOT deleted)."""
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        for item in self.items:
            self.layout.addWidget(item)
        self.layout.addStretch(1)

    def __track_at_position(self, y: int):
        for item in self.items:
            geo = item.geometry()
            if geo.top() <= y <= geo.bottom():
                return item
        return None