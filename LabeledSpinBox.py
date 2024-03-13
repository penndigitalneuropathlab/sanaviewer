
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QLabel, QSpinBox, QVBoxLayout

class LabeledSpinBoxWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, label_text="", default_value=0):
        super().__init__()

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.label = QLabel(label_text)
        self.main_layout.addWidget(self.label)

        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(0)
        self.spinbox.setMaximum(10)
        self.spinbox.setSingleStep(1)
        self.spinbox.setValue(default_value)
        self.main_layout.addWidget(self.spinbox)

        self.spinbox.valueChanged.connect(self.value_changed.emit)

    def get_value(self):
        return self.spinbox.value()
    def set_value(self, value):
        self.spinbox.setValue(value)
    def get_label(self):
        return self.label.text()
    def set_label(self, text):
        return self.label.setText(text)