
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QPushButton, QColorDialog

class ColorPickerPushButton(QPushButton):
    color_changed = pyqtSignal(QColor, name='color_changed')

    def __init__(self, default_color="", text=""):
        super().__init__(text)

        color =  QColor(default_color)
        self.set_color(color)

        self.clicked.connect(self.change_color)


    def change_color(self):
        new_color = QColorDialog().getColor(self.color)
        if new_color != self.color:
            self.set_color(new_color)

    def set_color(self, color: QColor):
        self.color = color
        self.setStyleSheet("background-color: " + color.name())
        self.color_changed.emit(self.color)