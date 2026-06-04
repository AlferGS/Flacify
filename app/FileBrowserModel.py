import os
import json
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "HIDE"
from pathlib import Path
from pygame import mixer, error as pyerror

class FileBrowserModel():
    def __init__(self):
        mixer.init()
        
        self.config = self.__load_config()
        self.current_pos = self.root_path


    @property
    def root_path(self) -> Path:
        return Path(self.config.get("library", "").get("root_path", ""))


    @property
    def excluded_folders(self) -> list[Path]:
        if self.config:
            return list(map(lambda path: Path(path), self.config.get("library", "").get("excluded_folders", [])))
        else:
            return []


    @property
    def supported_formats(self) -> list[str]:
        return self.config.get("library", "").get("supported_formats", [])


    def __load_config(self) -> dict:
        if not Path("config.json").exists():
            print("Config file not exist")
            raise FileNotFoundError("Config file not exist")
        
        try:
            with open("config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)

        except Exception as e:
            print(f"Can't open config file {e}")
            raise Exception(e)            

        return config
    

    def get_dir(self) -> dict:
        current_dir = dict()
        index = 0

        for file in self.current_pos.iterdir():

            if self.is_supported(file):
                current_dir[index] = file.name
                index += 1

        return current_dir


    def is_supported(self, file:Path) -> bool:
        if file.is_dir() and file not in self.excluded_folders:
            return True
        elif file.is_file() and file.suffix.lower() in self.supported_formats:
            return True
        else:
            return False


    def open_file(self, path:Path) -> None:
        assume_path = self.current_pos / path
        
        if assume_path.is_dir():
            self.current_pos = assume_path
        elif assume_path.is_file():
            self.play_sound(assume_path)


    def play_sound(self, file_path:Path) -> None:
        if not file_path.exists():
            print("File is not exist")
        
        mixer.music.load(file_path)
        mixer.music.play()
        print(f"playing file - {file_path.name}")


    def back_previous_dir(self) -> None:
        if self.current_pos != self.root_path:
            self.current_pos = self.current_pos.parent
        else:
            print("You are in root directory")


    def print_config(self) -> None:
        print(self.config)
        

if __name__ == "__main__":
    f = FileBrowserModel()
    f.get_dir()