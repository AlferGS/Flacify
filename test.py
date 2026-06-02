import sys
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "HIDE"
from PyQt5.QtWidgets import QPushButton, QWidget, QApplication, QHBoxLayout
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag
from pygame import mixer, error as pyerror

def play(path:str, song_name:str):
    file_path = os.path.join(path, song_name)
    
    if not os.path.exists(file_path):
        print("File not found")
        return
    
    mixer.music.load(file_path)
    mixer.music.play()

    print(f"\t Now playing: {song_name}")
    
    while True:
        command = input(">").upper()
        if command == 'P':
            mixer.music.pause()
            



class Example(QWidget):

    def __init__(self):
        super().__init__()
        try:
            self.__init_ui()
            mixer.init()

        except Exception as e:
            print(f'UnknownError: {e}')
            return
        
        except pyerror as e: 
            print("Audio initialization error: {e}")
            return


    def __init_ui(self):
        self.setGeometry(300, 300, 280, 150)

        layout = QHBoxLayout()
        self.play_button = QPushButton('Play', self)
        self.stop_button = QPushButton('Stop', self)

        self.play_button.clicked.connect(self.__on_start)
        self.stop_button.clicked.connect(self.__on_stop)
        
        layout.addStretch()
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)
        layout.addStretch()

        layout.setAlignment(Qt.AlignCenter)
        
        self.setLayout(layout)
    
    def __on_start(self, e):
        print('---song start playing---')
        mixer.music.unpause()

    def __on_stop(self, e):
        print('song stop playing')
        mixer.music.pause()

    def play_music(self, path="music", filename="WASP1992-09_Hold On To My Heart.mp3"):
        if not os.path.isdir(path):
            print(f"folder ({path}) is not found")
            return

        else:
            print("path correct")
        
        mp3_files_list = [file for file in os.listdir(path) if file.endswith(".mp3") ]
        
        if not mp3_files_list:
            print("folder is empty")

        while True:
            print("***** MP3 PLAYER *****")
            print("My song list:")

            for index, song in enumerate(mp3_files_list, start=1):
                print(f"{index}) {song}")

            choice_input = input("\nEnter the song # to play (or 'Q' to quit): ")

            if choice_input.upper() == 'Q':
                print('Quit')
                return
            elif not choice_input.isdigit():
                print('Try again')
                continue
            
            choice = int(choice_input) - 1
            if 0 <= choice < len(mp3_files_list):
                print(f"Start playing song - {mp3_files_list[choice]}")
                play(path, mp3_files_list[choice])
            else:
                print('Try again')
                continue




if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    ex.play_music()
    app.exec_()