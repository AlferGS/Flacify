import sys
from PyQt5.QtWidgets import QMainWindow, QAction, QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__initUI()


    def __initUI(
            self,
            x_size: int = 600,
            y_size: int = 600,
            x_offset: int = 0,
            y_offset: int = 0,
            is_center: bool = True,
            window_title: str = 'Flacify') -> None:
        ''' Set base parameters for main window
        '''
        self.apply_spotify_theme()
        # Set window parameters
        self.resize(x_size, y_size)
        self.setWindowTitle(window_title)
        if is_center:
            self.__center_window()
        else:
            self.move(x_offset, y_offset)
        
        # Set menubar, toolbar, statusbar
        qaction_dict = dict()
        qaction_dict['quit_action'] = self.__create_QuitEvent()

        self.__create_menubar(qaction_dict)
        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(qaction_dict['quit_action'])
        
        self.statusBar().showMessage('Ready to drive?')

        okButton = QPushButton("OK")
        cancelButton = QPushButton("Cancel")
        okButton.setObjectName('primaryBtn')

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(okButton)
        hbox.addWidget(cancelButton)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)

        central_widget = QWidget()
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

        self.show()


    def apply_spotify_theme(self):
        """Применяет темную тему в стиле Spotify"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #121212;
                color: #FFFFFF;
            }

            QPushButton {
                background-color: #181818;
                color: #FFFFFF;
                border: none;
                padding: 10px 24px;
                border-radius: 25px;
                font-weight: bold;
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: #282828;
            }

            QPushButton:pressed {
                background-color: #1DB954;
                color: #000000;
            }

            /* Специальный класс для зеленой кнопки */
            QPushButton#primaryBtn {
                background-color: #1DB954;
                color: #000000;
            }

            QPushButton#primaryBtn:hover {
                background-color: #1ED760;
            }

            QLabel {
                color: #B3B3B3;
            }

            QMenuBar {
                background-color: #121212;
                color: #FFFFFF;
            }
            
            QMenuBar::item:selected {
                background: #282828;
            }

            QMenu {
                background-color: #282828;
                color: #FFFFFF;
                border: 1px solid #3E3E3E;
            }
            
            QMenu::item:selected {
                background-color: #3E3E3E;
            }
        """)

    def __center_window(self) -> None:
        ''' Centers the window on the primary screen
        '''
        screen = QApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        window_rect.moveCenter(screen.center())
        self.move(window_rect.topLeft())


    def __create_QuitEvent(self) -> QAction:
        ''' Change Exit icon and set shortcut to quit application
        '''
        try:
            exit_action = QAction(QIcon("images/exit.png"), '&Exit', self)
            exit_action.setShortcut('Ctrl+Q')
            exit_action.setStatusTip('Exit Application')
            exit_action.triggered.connect(QApplication.instance().quit)
            return exit_action
        except Exception as e:
            print(f'__set_QuitEvent: {e}')


    def __create_menubar(self, actions: dict[str:QAction]) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(actions['quit_action'])



def main(*args,**kwargs):
    print('__main__: start application')
    try:
        app = QApplication(sys.argv)

        main_window = MainWindow()

    except Exception as e:
        print (f'Error on application start ({e})')
    finally:
        try:
            sys.exit(app.exec_())

        except Exception as e:
            print('Error on closing application ({e})')
        finally:
            print('__main__: close application')

    


if __name__ == "__main__":
    main()