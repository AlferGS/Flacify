#components/create_playlist_dialog.py
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    FluentIcon,
    LineEdit,
    MessageBoxBase,
    PushButton,
    SubtitleLabel,
    TogglePushButton,
)

# Pre-installed color palette
PRESET_COLORS = [
    "#1DB954",  # Spotify Green
    "#1E90FF",  # Blue
    "#FF4757",  # Red
    "#A55EEA",  # Purple
    "#FF9F43",  # Orange
    "#FECA57",  # Yellow
    "#FF6B81",  # Pink
    "#00D2D3",  # Teal
    "#576574",  # Gray
    "#222F3E",  # Dark
]


class ColorSwatch(QWidget):
    """Round color-sampler button."""

    clicked = pyqtSignal(str)

    def __init__(self, color: str, size: int = 32, parent=None):
        super().__init__(parent)
        self._color = color
        self._selected = False
        self._size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.update()

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPen
        from PyQt5.QtCore import QRectF

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(2, 2, self._size - 4, self._size - 4)
        painter.setBrush(QColor(self._color))

        if self._selected:
            painter.setPen(QPen(QColor("#FFFFFF"), 3))
        else:
            painter.setPen(Qt.NoPen)

        painter.drawEllipse(rect)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._color)


class CreatePlaylistDialog(MessageBoxBase):
    """
    A dialog for creating a new playlist or editing an existing one.
    Contains a name field and a color palette.

    Signals:
        playlist_confirmed(str, str) — (name, color) upon confirmation.
    """

    playlist_confirmed = pyqtSignal(str, str)

    def __init__(
        self,
        existing_name: str = "",
        existing_color: str = "#1DB954",
        parent=None,
    ):
        super().__init__(parent)
        self._selected_color = existing_color
        self._swatches: list[ColorSwatch] = []

        # header
        title = "Edit playlist" if existing_name else "New playlist"
        self.titleLabel = SubtitleLabel(title, self)
        self.titleLabel.setContentsMargins(0, 0, 0, 12)

        # playlist name field
        name_label = QLabel("Playlist name")
        name_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        self.name_input = LineEdit(self)
        self.name_input.setPlaceholderText("Enter playlist name...")
        self.name_input.setText(existing_name)
        self.name_input.setFixedHeight(36)
        self.name_input.setStyleSheet(
            "LineEdit { background: #1F1F1F; border: 1px solid #333; "
            "border-radius: 6px; color: #FFF; padding: 4px 8px; }"
            "LineEdit:focus { border: 1px solid #1DB954; }"
        )

        color_label = QLabel("Color")
        color_label.setStyleSheet("color: #AAAAAA; font-size: 12px; margin-top: 8px;")

        self._palette_layout = QHBoxLayout()
        self._palette_layout.setSpacing(6)
        self._build_palette()

        self.yesButton.setText("Save" if existing_name else "Create")
        self.cancelButton.setText("Cancel")

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(name_label)
        self.viewLayout.addWidget(self.name_input)
        self.viewLayout.addWidget(color_label)
        self.viewLayout.addLayout(self._palette_layout)
        self.viewLayout.addSpacing(8)

        # button signals
        self.yesButton.clicked.connect(self._on_confirm)

        # start playlist badge color
        self._select_color(existing_color)

        self.widget.setMinimumWidth(380)

    # Protected

    def _build_palette(self) -> None:
        for color in PRESET_COLORS:
            swatch = ColorSwatch(color, size=32)
            swatch.clicked.connect(self._on_swatch_clicked)
            self._swatches.append(swatch)
            self._palette_layout.addWidget(swatch)

    def _on_swatch_clicked(self, color: str) -> None:
        self._select_color(color)

    def _select_color(self, color: str) -> None:
        self._selected_color = color
        for swatch in self._swatches:
            swatch.set_selected(swatch._color == color)

    def _on_confirm(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            return  # do not close if it hasn't playlist name
        self.playlist_confirmed.emit(name, self._selected_color)
        self.accept()