#components/list_item.py
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QBrush, QCursor, QIcon
from PyQt5.QtWidgets import QHBoxLayout
from qfluentwidgets import BodyLabel, CardWidget, FluentIcon as FIF, IconWidget, TransparentToolButton


class ListItemBase(CardWidget):
    """Base list row: hover background + optional hover '...' button.
    context_menu_requested(global QPoint) fires on right-click AND on '...' click."""
    context_menu_requested = pyqtSignal(object)
    drag_started = pyqtSignal(object)
    drag_moved = pyqtSignal(object, object)   # (item, global QPoint)
    drag_finished = pyqtSignal(object)

    def __init__(self, menu_enabled: bool = False, height: int = 46,
                 drag_enabled: bool = False, parent=None):
        super().__init__(parent)
        self._menu_enabled = menu_enabled
        self._drag_enabled = drag_enabled
        self._drag_active = False
        self._drag_start_pos = None
        self.setFixedHeight(height)
        self.setMinimumWidth(100)
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setSpacing(8)
        self.h_layout.setContentsMargins(10, 4, 6, 4)
        # Hover '...' button (added to layout by subclass at the end)
        self.menu_button = TransparentToolButton(FIF.MORE)
        self.menu_button.setFixedSize(28, 28)
        # Space is always reserved; icon and clicks enabled only on hover
        self.menu_button.setIcon(QIcon())
        self.menu_button.setEnabled(False)
        self.menu_button.clicked.connect(self.__on_menu_clicked)

    # ==================== Events ====================
    def __on_menu_clicked(self):
        if not self._menu_enabled:
            return
        self.context_menu_requested.emit(QCursor.pos())
   
    def enterEvent(self, event):
        super().enterEvent(event)
        if self._menu_enabled:
            self.menu_button.setIcon(FIF.MORE)
            self.menu_button.setEnabled(True)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.menu_button.setIcon(QIcon())
        self.menu_button.setEnabled(False)

    def mousePressEvent(self, event):
        if self._drag_enabled and event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
            self._drag_active = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (self._drag_enabled and self._drag_start_pos is not None
                and (event.buttons() & Qt.LeftButton)):
            if not self._drag_active and \
               (event.pos() - self._drag_start_pos).manhattanLength() > 5:
                self._drag_active = True
                self.setCursor(Qt.SizeAllCursor)
                self.drag_started.emit(self)
            if self._drag_active:
                self.drag_moved.emit(self, event.globalPos())
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        was_dragging = self._drag_active
        self._drag_active = False
        self._drag_start_pos = None
        if was_dragging:
            self.setCursor(Qt.ArrowCursor)
            self.drag_finished.emit(self)
            event.accept()
            return  # suppress CardWidget.clicked after a drag
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        self.context_menu_requested.emit(event.globalPos())
        event.accept()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 6, 6)
        if self.isHover or self.isPressed:
            bg_color = QColor("#1F1F1F")
        else:
            bg_color = QColor("#111111")
        painter.fillPath(path, QBrush(bg_color))


class FolderListItem(ListItemBase):
    """Folder row: icon (swaps to arrow on hover) + name."""
    itemClicked = pyqtSignal(str)

    def __init__(self, folder_name: str, parent=None):
        super().__init__(menu_enabled=False, height=46, parent=parent)
        self.folder_name = folder_name
        self.setObjectName("FolderListItem")

        self.icon = IconWidget()
        self.icon.setIcon(FIF.MUSIC_FOLDER)
        self.icon.setFixedSize(20, 20)
        self.h_layout.addWidget(self.icon)
        self.h_layout.addSpacing(5)

        self.label = BodyLabel(self.folder_name)
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.label.setContentsMargins(0, 0, 0, 0)
        self.label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self.h_layout.addWidget(self.label)

        self.h_layout.addStretch(1)
        self.h_layout.addWidget(self.menu_button)

        self.clicked.connect(self.__on_clicked)

    def __on_clicked(self):
        self.itemClicked.emit(self.folder_name)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.icon.setIcon(FIF.RIGHT_ARROW)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.icon.setIcon(FIF.MUSIC_FOLDER)