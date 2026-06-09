import os
import json
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFileDialog
)
from PyQt5.QtCore import Qt
from qfluentwidgets import (
    PushButton, 
    TransparentToolButton,
    FluentIcon as FIF
)

# Settings page
class SettinsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.__init_ui()


    def __init_ui(self):
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


    def __create_default_config(self) -> dict:
        config_data = dict()
        config_data["library"] = {}
        config_data["library"]["root_path"] = "/home/alfer/Документы/Projects Python/Flacify/music"
        print(config_data)
        return config_data


    def __create_path_layout(self) -> QHBoxLayout:
        path_layout = QHBoxLayout()
        path_layout.setAlignment(Qt.AlignLeft)

        # Label
        self.path_label = QLabel("Path to audio folder:")
        self.path_label.setStyleSheet("color: #FFFFFF; font-size: 12px;")
        # LineEdit
        self.path_lineedit = QLineEdit(" {default_path}") # add default path from config.json
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
        # Button
        self.path_btn = TransparentToolButton(FIF.MEDIA)
        self.path_btn.clicked.connect(self.__on_path_btn_clicked)

        # Add widgets to layout
        path_layout.addWidget(self.path_label)
        path_layout.addSpacing(5)
        path_layout.addWidget(self.path_lineedit)
        path_layout.addSpacing(5)
        path_layout.addWidget(self.path_btn)
        path_layout.addStretch()

        return path_layout


    def __get_root_path(self) -> str:
        config_file = "config.json"

        
        return ""


    def __create_save_config_layout(self) -> QHBoxLayout:
        save_config_layout = QHBoxLayout()
        # Save btn
        save_btn = TransparentToolButton(FIF.SAVE)
        save_btn.resize(150,50)
        save_btn.clicked.connect(self.__on_save_btn_clicked)

        save_config_layout.addStretch()
        save_config_layout.addWidget(save_btn)

        return save_config_layout


    def __on_path_btn_clicked(self):
        self.show_dialog()


    def show_dialog(self):
        # Open file dialog
        file_path = QFileDialog.getExistingDirectory(self, 'Open File', '')
        # file_path, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'All Files (*)')
        if file_path: self.path_lineedit.setText(f'{file_path}')


    def __on_save_btn_clicked(self):
        path_ = self.path_lineedit.text()
        config_file = "config.json"

        if not os.path.exists(path_):
            print("Ошибка: Папка не существует")
            return
        
        config_data = None

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            except FileNotFoundError as e:
                with open(config_file, 'w', encoding='utf-8') as f:
                    config_data = self.__create_default_config()
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                print(f"Config file not found: {e}")
            
            except json.JSONDecodeError as e:
                print(f"Error to read JSON. File are damaged. {e}")

            except Exception as e:
                print(f"Unknown error - {e}")
        
        if config_data is None:
            config_data = self.__create_default_config() 

        config_data.setdefault("library", {})["root_path"] = path_

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            print("Config was saved!")
        except Exception as e:
            print(f"Unknown error - {e}")

        




