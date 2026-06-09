import os
import sys
import time
from pathlib import Path
from FileBrowserModel import FileBrowserModel

# Import msvcrt only for Windows
if os.name == 'nt':
    import msvcrt

# For Linux/Mac imports tty/termios
else:
    import termios
    import tty
    import select

def print_dir(current_dir:dict):
    if not current_dir:
        print("Directory is empty or inaccessible")
        return
    
    for idx, obj in current_dir.items():
        print(f"{idx}: {obj}")


def get_key_non_blocking():
    """
    Return pressed key without blocking main thread.
    Return None if no key is pressed.
    Works on Windows and Linux.
    """
    if os.name == 'nt':
        # Windows: msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getwch()
            # Ignore special prefix bytes for arrow keys etc.
            if key in ('\x00', '\xe0'):
                _ = msvcrt.getwch()
                return None
            return key.lower()
    
    else:
        # Linux/Unix: termios + select
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)  # non-blocking, character-at-a-time mode
            
            # Check if input is available (timeout = 0)
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                # Handle escape sequences (arrows, etc.)
                if key == '\x1b':  # ESC character
                    # Read next chars to consume the sequence
                    if select.select([sys.stdin], [], [], 0.01)[0]:
                        sys.stdin.read(1)  # skip '['
                    if select.select([sys.stdin], [], [], 0.01)[0]:
                        sys.stdin.read(1)  # skip arrow code
                    return None
                return key.lower()
        except Exception:
            # Fallback: restore settings and return None
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return None
        finally:
            # Always restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    return None


def print_console_ui(file_browser):
    # Clear console
    os.system('cls')  

    print("=== FLACIFY CONSOLE TEST ===")
    print(f"Current Dir: {file_browser.current_pos}")
    print("-" * 30)
    print_dir(file_browser.current_dir)
    print("-" * 30)

    status = "Playing" if (file_browser.audio_player and file_browser.audio_player.is_playing) else "Stopped"
    track_idx = file_browser.audio_player.current_track_index if file_browser.audio_player else "-"
    if file_browser.audio_player:
        current_track_name = file_browser.audio_player.get_song_name()
        print(f"Current track name: { current_track_name}")
        print(f"Message: {file_browser.audio_player.message}")

    print(f"Status: {status} | Track Index: {track_idx}")
    print("\n[o] Open | [b] Back | [n] Next | [p] Prev | [q] Quit")


def main():
    file_browser = FileBrowserModel()
    print("Start of non-blocking test")
    print("Controls: [o]pen, [b]ack, [n]ext, [p]rev, [q]uit")
    print("(No need to press Enter)")
    
    last_print_time = 0
    
    while True:
        file_browser.update()
        
        key = get_key_non_blocking()
        
        if key:
            if key == 'q':
                break
            
            elif key == 'o':
                try:
                    # stop while cycle for input 
                    index_str = input("\nEnter index to open: ")
                    index = int(index_str)
                    
                    current_dir = file_browser.current_dir
                    if index in current_dir:
                        file_browser.open_file(index)
                    else:
                        print("Incorrect index")
                except ValueError:
                    print("Invalid number")
                    
            elif key == 'b':
                file_browser.back_previous_dir()
                
            elif key == 'n':
                file_browser.next_song()
                
            elif key == 'p':
                file_browser.prev_song()
            
            # Force update UI 
            last_print_time = 0 

        # Full update console UI
        current_time = time.time()
        if current_time - last_print_time > 1.0:
            print_console_ui(file_browser)
            last_print_time = current_time
            
        time.sleep(0.1)

    print("End of test")

if __name__ == '__main__':
    main()
