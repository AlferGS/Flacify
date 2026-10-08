#components/round_tool_button.py
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QPushButton
from qfluentwidgets import FluentIcon, Theme


class RoundToolButton(QPushButton):
    """Circular icon button with reliable QSS background/border-radius.

    TransparentToolButton paints its own background, so QSS border-radius
    is not always enough for a perfect circle. QPushButton respects QSS
    background + border-radius predictably.
    """

    def __init__(
        self,
        icon: FluentIcon,
        size: int,
        normal: str = "#1DB954",
        hover: str = "#1ED760",
        pressed: str = "#169C46",
        disabled: str = "#3A3A3A",
        parent=None,
    ):
        super().__init__(parent)

        self._fluent_icon = icon
        self._size = size

        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setText("")
        self.setIconSize(QSize(max(14, size // 2), max(14, size // 2)))
        self.set_fluent_icon(icon)

        radius = size // 2
        self.setStyleSheet(f"""
            RoundToolButton {{
                background-color: {normal};
                border: none;
                border-radius: {radius}px;
                padding: 0px;
                outline: none;
            }}
            RoundToolButton:hover {{
                background-color: {hover};
            }}
            RoundToolButton:pressed {{
                background-color: {pressed};
            }}
            RoundToolButton:disabled {{
                background-color: {disabled};
            }}
            RoundToolButton:focus {{
                border: none;
                outline: none;
            }}
        """)

    def set_fluent_icon(self, icon: FluentIcon) -> None:
        """Set FluentIcon and keep reference for possible theme refresh."""
        self._fluent_icon = icon
        super().setIcon(icon.icon(Theme.DARK))