
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QCheckBox, QHBoxLayout, QVBoxLayout, QDockWidget

from sana.color_deconvolution import StainSeparator

from superqt import QRangeSlider

class ColorDeconvolutionDockWidget(QDockWidget):
    def __init__(self, name=""):
        super().__init__(name)
    
        self.widget = ColorDeconvolutionWidget()

        self.setWidget(self.widget)

class ColorDeconvolutionWidget(QWidget):
    MIN_SLIDER_VAL = 0
    MAX_SLIDER_VAL = 100
    MIN_OD_VAL = 0.0
    MAX_OD_VAL = 2.0

    def __init__(self):
        super().__init__()

        self.ss = StainSeparator('H-DAB')
        self.stains = ['HEM', 'DAB', 'RES']

        self.main_layout = QVBoxLayout()

        self.stain_A_layout = QHBoxLayout()

        self.stain_A_label = QLabel(self.stains[0])
        self.stain_A_layout.addWidget(self.stain_A_label)
        
        # convert -1 -> 5 to 0 -> 100, function to go back and forth

        self.stain_A_slider = QRangeSlider(Qt.Orientation.Horizontal)
        self.stain_A_slider.setMinimum(self.MIN_SLIDER_VAL)
        self.stain_A_slider.setMaximum(self.MAX_SLIDER_VAL)
        self.stain_A_slider.setValue((self.MIN_SLIDER_VAL, self.MAX_SLIDER_VAL))
        self.stain_A_layout.addWidget(self.stain_A_slider)
        
        self.stain_A_checkbox = QCheckBox()
        self.stain_A_checkbox.setChecked(True)
        self.stain_A_layout.addWidget(self.stain_A_checkbox)

        self.main_layout.addLayout(self.stain_A_layout)

        self.stain_B_layout = QHBoxLayout()

        self.stain_B_label = QLabel(self.stains[1])
        self.stain_B_layout.addWidget(self.stain_B_label)
        
        self.stain_B_slider = QRangeSlider(Qt.Orientation.Horizontal)
        self.stain_B_slider.setMinimum(self.MIN_SLIDER_VAL)
        self.stain_B_slider.setMaximum(self.MAX_SLIDER_VAL)
        self.stain_B_slider.setValue((self.MIN_SLIDER_VAL, self.MAX_SLIDER_VAL))
        self.stain_B_layout.addWidget(self.stain_B_slider)
        
        self.stain_B_checkbox = QCheckBox()
        self.stain_B_checkbox.setChecked(True)
        self.stain_B_layout.addWidget(self.stain_B_checkbox)

        self.main_layout.addLayout(self.stain_B_layout)

        self.stain_C_layout = QHBoxLayout()

        self.stain_C_label = QLabel(self.stains[2])
        self.stain_C_layout.addWidget(self.stain_C_label)
        
        self.stain_C_slider = QRangeSlider(Qt.Orientation.Horizontal)
        self.stain_C_slider.setMinimum(self.MIN_SLIDER_VAL)
        self.stain_C_slider.setMaximum(self.MAX_SLIDER_VAL)
        self.stain_C_slider.setValue((self.MIN_SLIDER_VAL, self.MAX_SLIDER_VAL))
        self.stain_C_layout.addWidget(self.stain_C_slider)
        
        self.stain_C_checkbox = QCheckBox()
        self.stain_C_checkbox.setChecked(True)
        self.stain_C_layout.addWidget(self.stain_C_checkbox)

        self.main_layout.addLayout(self.stain_C_layout)

        self.setLayout(self.main_layout)

    def od_to_slider(self, val):
        rescaled_od = (val - self.MIN_OD_VAL) / (self.MAX_OD_VAL - self.MIN_OD_VAL)
        return rescaled_od * (self.MAX_SLIDER_VAL - self.MIN_SLIDER_VAL) + self.MIN_SLIDER_VAL
    
    def slider_to_od(self, val):
        rescaled_slider = (val - self.MIN_SLIDER_VAL) / (self.MAX_SLIDER_VAL - self.MIN_SLIDER_VAL)
        return rescaled_slider * (self.MAX_OD_VAL - self.MIN_OD_VAL) + self.MIN_OD_VAL

        
