#main.py
import sys
import traceback

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

from app.windows import MainFluentWindow


def main() -> int:
    print('__main__: start application')

    try:
        app = QApplication(sys.argv)
    except Exception:
        traceback.print_exc()
        print('Error on application start (QApplication)')
        return 1

    font = QFont("Circular", 10)
    app.setFont(font)

    try:
        window = MainFluentWindow()
    except Exception:
        traceback.print_exc()
        print('Error on application start (MainFluentWindow)')
        return 1

    window.setStyleSheet("background-color: #000000")
    window.show()

    try:
        return app.exec_()
    except Exception:
        traceback.print_exc()
        print('Error on closing application')
        return 1
    finally:
        print('__main__: close application')


if __name__ == "__main__":
    sys.exit(main())