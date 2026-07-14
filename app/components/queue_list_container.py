# components/queue_list_container.py
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

from .queue_track_item import QueueTrackItem

class QueueListContainer(QWidget):
    """Container for track list. Manages their order."""
    order_changed = pyqtSignal(list)
    track_double_clicked = pyqtSignal(Path)

    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4) 
        self.layout.setSpacing(4)
        self.items = []
        self.dragged_item = None
        
        # Allows the container to stretch in width within the ScrollArea
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(200) 


    def __on_drag_started(self, item):
        """Start Drag event. Save draged item"""
        self.dragged_item = item


    def __on_drag_moved(self, item, global_pos):
        """Change elements when draged element moved."""
        local_pos = self.mapFromGlobal(global_pos)
        current_index = self.items.index(item)
        
        for i, other_item in enumerate(self.items):
            if other_item is item:
                continue
            
            other_rect = other_item.geometry()
            other_center_y = other_rect.center().y()
            
            # Check if the cursor is within the vertical range of another element
            if other_rect.contains(local_pos):
                # If we drag down
                if current_index < i and local_pos.y() > other_center_y:
                    self.items.remove(item)
                    self.items.insert(i, item)
                    self.__rebuild_layout()
                    break
                # If we drag up
                elif current_index > i and local_pos.y() < other_center_y:
                    self.items.remove(item)
                    self.items.insert(i, item)
                    self.__rebuild_layout()
                    break


    def __on_drag_finished(self, item):
        """Drop the element in queue."""
        if self.dragged_item:
            new_order = [item.track_path for item in self.items]
            self.order_changed.emit(new_order)
            self.dragged_item = None


    def __on_track_double_clicked(self, track_path: Path):
        """Throw the double-click signal emit."""
        self.track_double_clicked.emit(track_path)


    def __rebuild_layout(self):
        """Clears and create new queue list on layout level."""
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        for item in self.items:
            self.layout.addWidget(item)
        
        self.layout.addStretch()


    def _update_current_highlight(self, current_path: Path):
        """Update current highlight and text color by the state is_current for all elements of queue."""
        for item in self.items:
            old_is_current = item.is_current
            item.is_current = (item.track_path == current_path)
            if old_is_current != item.is_current:
                item._update_text_colors()  
                item.update()


    def _set_tracks(self, tracks: list[Path], current_track: Path):
        """Clears and refills the track list."""
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        self.items.clear()
        for track in tracks:
            item = QueueTrackItem(track, track == current_track)
            item.drag_started.connect(self.__on_drag_started)
            item.drag_moved.connect(self.__on_drag_moved)
            item.drag_finished.connect(self.__on_drag_finished)
            item.track_double_clicked.connect(self.__on_track_double_clicked)
            self.layout.addWidget(item)
            self.items.append(item)
        self.layout.addStretch()
            