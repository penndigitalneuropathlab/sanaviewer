
import os
import sys

from PyQt6.QtWidgets import QApplication
from ImageViewer import ImageViewer

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec())

    # TODO QScrollArea support mouse
    # base on https://github.com/baoboa/pyqt5/blob/master/examples/widgets/imageviewer.py
    #
    # if you need Two Image Synchronous Scrolling in the window by PyQt5 and Python 3
    # please visit https://gist.github.com/acbetter/e7d0c600fdc0865f4b0ee05a17b858f2