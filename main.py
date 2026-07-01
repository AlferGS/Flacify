import sys
from PyQt5.QtWidgets import QApplication
from app.main_window import MainFluentWindow
from PyQt5.QtGui import QFont, QColor

def main(*args,**kwargs):
    print('__main__: start application')
    try:
        app = QApplication(sys.argv)
        font = QFont("Circular", 10)
        app.setFont(font)

        main_app = MainFluentWindow()
        main_app.setStyleSheet("background-color: #000000")
        # main_app.setBackgroundColor(QColor("#000000"))
        main_app.show()


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