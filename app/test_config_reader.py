from pathlib import Path

from FileBrowserModel import FileBrowserModel

def print_dir(current_dir:dict):
    for idx, obj in current_dir.items():
        print(f"{idx}. {obj}")

def main():
    file_browser = FileBrowserModel()
    print("Start of test")

    while True:
        current_dir = file_browser.get_dir()

        print("This dir:")
        print_dir(current_dir)
        inp = input("Enter O(open), b(back), q(quit): ")

        if inp.upper() == "Q":
            break

        elif inp.upper() == "O":
            try:
                num:int = int(input("Enter num of folder/file: "))
            except ValueError:
                print("Invalid value. Try again")
                continue

            if num not in current_dir:
                print("Incorrect num.")
                continue

            file_browser.open_file(Path(current_dir[num]))

        elif inp.upper() == "B":
            file_browser.back_previous_dir()

        else:
            pass
        
    print("End of test") 


if __name__ == '__main__':
    main()