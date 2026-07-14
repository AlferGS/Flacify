#windows/settings_window.py
import os
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QFileDialog, QVBoxLayout, QWidget

from qfluentwidgets import FluentIcon as FIF, TransparentToolButton

from app.core.app_state import AppState

class SettingsWindow(QWidget):
    """Settings page in main_fluent_window."""
    def __init__(self, app_state: AppState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.__init_ui()


    def __init_ui(self):
        """Init UI part of page."""
        self.setObjectName("Settings Window")
        self.setContentsMargins(15, 5, 15, 5)

        self.vbox = QVBoxLayout(self)
        self.vbox.setAlignment(Qt.AlignTop)

        main_label = QLabel("<b>Settings<\b>")
        main_label.setAlignment(Qt.AlignLeft)
        main_label.setStyleSheet("color: #FFFFFF; font-size: 16px;")
        
        path_layout = self.__create_path_layout()
        save_config_layout = self.__create_save_config_layout()

        self.vbox.addWidget(main_label)
        self.vbox.addLayout(path_layout)
        self.vbox.addStretch()
        self.vbox.addLayout(save_config_layout)


    def __create_path_layout(self) -> QHBoxLayout:
        """Create layout with path line edit and button for QFileDialog."""
        path_layout = QHBoxLayout()
        path_layout.setAlignment(Qt.AlignLeft)

        self.path_label = QLabel("Path to audio folder:")
        self.path_label.setStyleSheet("color: #FFFFFF; font-size: 12px;")

        current_path = str(self.app_state.root_path)
        self.path_lineedit = QLineEdit(current_path if current_path else "")
        self.path_lineedit.setPlaceholderText("Select audio library folder...")
        self.path_lineedit.setStyleSheet("""
            QLineEdit {
                background-color: #131313; 
                color: #FFFFFF; 
                font-size: 12px;
                border: 1px solid #ACACAC;
                border-radius: 4px;
            }
        """)
        self.path_lineedit.setMinimumWidth(500)
        self.path_lineedit.setEnabled(False)
        # QFileDialog Button
        self.path_btn = TransparentToolButton(FIF.MEDIA)
        self.path_btn.clicked.connect(self.__on_path_btn_clicked)

        path_layout.addWidget(self.path_label)
        path_layout.addSpacing(5)
        path_layout.addWidget(self.path_lineedit)
        path_layout.addSpacing(5)
        path_layout.addWidget(self.path_btn)
        path_layout.addStretch()

        return path_layout


    def __create_save_config_layout(self) -> QHBoxLayout:
        """A page control layout. Placed at the bottom of the page."""
        save_config_layout = QHBoxLayout()

        save_btn = TransparentToolButton(FIF.SAVE)
        save_btn.resize(150,50)
        save_btn.clicked.connect(self.__on_save_btn_clicked)

        save_config_layout.addStretch()
        save_config_layout.addWidget(save_btn)

        return save_config_layout


    def __on_path_btn_clicked(self):
        """Path Button clicked event.
        Open QFileDialog for selecting root_path.
        """
        start_dir = str(self.app_state.root_path) or ""
        root_path = QFileDialog.getExistingDirectory(self, 'Select Audio Library', start_dir)
        if root_path:
            self.path_lineedit.setText(root_path)


    def __on_save_btn_clicked(self):
        """Save Button clicked event.
        Check path and save it in app_state with config file. 
        """
        path_ = Path(self.path_lineedit.text().strip())

        if not path_ or not os.path.isdir(path_):
            print("[SettingsWindow] Error: Folder isn't exist")
            return

        self.app_state.root_path = str(path_)
        self.app_state._save()
        
        print(f"[SettingsWindow] Config saved! root_path = {path_}")