
import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QLabel, QCheckBox, QHBoxLayout, QVBoxLayout, QDockWidget, QDoubleSpinBox, QSpinBox, QComboBox

from ColorPicker import ColorPickerPushButton

from sana.image import Frame

import pdnl_io

from matplotlib import pyplot as plt

class OverlayDockWidget(QDockWidget):
    def __init__(self, name=""):
        super().__init__(name)

        self.widget = OverlayWidget()

        self.setWidget(self.widget)

class OverlayWidget(QWidget):
    VALID_SUFFIXES = [
        'AUTO_THRESH',
        'HORIZONTAL_THRESH',
        'VERTICAL_THRESH',
    ]
    def __init__(self):
        super().__init__()

        self.entry_layout = QVBoxLayout()

        self.setLayout(self.entry_layout)

        self.measurements_widget = QComboBox()
        self.entry_layout.addWidget(self.measurements_widget)

        self.entry_widgets = []


    def set_entries(self, d, measurement=""):
        self.d = d

        # clear the widgets
        for widget in self.entry_widgets:
            self.entry_layout.removeWidget(widget)
            # TODO: delete widget?
        self.entry_widgets = []

        self.set_roi_entries(d)
        if measurement == "":
            self.set_measurements(d)
            measurement = self.measurements[0]
        self.set_overlay_entries(d, measurement)

    def set_roi_entries(self, d):
        for f in os.listdir(d):
            if f.endswith('.npz'):
                suffix = pdnl_io.get_slide_suffix(f)
                if 'MAIN' in suffix:
                    widget = OverlayEntryWidget(os.path.join(d, f), 'MAIN_ROI', outlines_only=True, default_color='black')
                    self.entry_layout.addWidget(widget)
                    self.entry_widgets.append(widget)
                if 'SUB' in suffix:
                    widget = OverlayEntryWidget(os.path.join(d, f), 'SUB_ROI', outlines_only=True, default_color='gray')
                    self.entry_layout.addWidget(widget)
                    self.entry_widgets.append(widget)
                if 'IGNORE' in suffix:
                    widget = OverlayEntryWidget(os.path.join(d, f), 'IGNORE_ROI', outlines_only=True, default_color='black')
                    self.entry_layout.addWidget(widget)
                    self.entry_widgets.append(widget)

    def set_measurements(self, d):
        self.measurements = []
        for measurement_d in sorted(os.listdir(d)):
            if measurement_d != 'AO':
                continue
            if os.path.isdir(os.path.join(d, measurement_d)):
                self.measurements.append(measurement_d)

        try:
            self.measurements_widget.currentTextChanged.disconnect()
        except:
            pass
        self.measurements_widget.clear()
        self.measurements_widget.addItems(self.measurements)
        self.measurements_widget.currentTextChanged.connect(self.update_overlay_entries_wrapper)

    # TODO: support soma centers
    # TODO: support grayscale?
    def set_overlay_entries(self, d, measurement):

        # find the files
        overlay_files = []
        for f in os.listdir(os.path.join(d, measurement)):
            if f.endswith('.npz'):
                suffix = pdnl_io.get_slide_suffix(f)
                overlay_files.append((suffix, f))

        # create the widgets
        for suffix, f in overlay_files:
            widget = OverlayEntryWidget(os.path.join(d, measurement, f), suffix)
            self.entry_layout.addWidget(widget)
            self.entry_widgets.append(widget)

    # TODO: eventually merge set and update after upgrading the functions
    def update_entries(self, d):
        self.d = d 
        self.set_roi_entries(d)
        self.set_measurements(d)
        self.set_overlay_entries(d, self.measurements[0])
        # self.update_roi_entries(d)
        # self.set_measurements(d)
        # self.update_overlay_entries(d, self.measurements[0])
    
    # TODO: delete entries that don't amtch
    # TODO: add entries that don't already exist
    def update_roi_entries(self, d):
        for f in os.listdir(d):
            if f.endswith('.npz'):
                suffix = pdnl_io.get_slide_suffix(f)
                if 'MAIN' in suffix:
                    for widget in self.entry_widgets:
                        if widget.get_label() == 'MAIN_ROI':
                            widget.load_frame(os.path.join(d, f))
                            break
                if 'SUB' in suffix:
                    for widget in self.entry_widgets:
                        if widget.get_label() == 'SUB_ROI':
                            widget.load_frame(os.path.join(d, f))
                            break
                if 'IGNORE' in suffix:
                    for widget in self.entry_widgets:
                        if widget.get_label() == 'IGNORE_ROI':
                            widget.load_frame(os.path.join(d, f))
                            break
            # TODO: delete entries that don't match

    # TODO: update this once upgraded
    def update_overlay_entries_wrapper(self, measurement):
        d = self.d
        self.set_entries(d, measurement=measurement)
        # self.update_overlay_entries(d, measurement)

    def update_overlay_entries(self, d, measurement):
        for f in os.listdir(os.path.join(d, measurement)):
            if f.endswith('.npz'):
                suffix = pdnl_io.get_slide_suffix(f)
                for widget in self.entry_widgets:
                    print(widget.get_label(), suffix)
                    if widget.get_label() == suffix:
                        print('aslkdjffajsdljklfds')
                        widget.load_frame(os.path.join(d, measurement, f))
        # TODO: delete entries that don't match

# TODO: needs a up/down arrow that sends a signal to re-order the widgets
class OverlayEntryWidget(QWidget):
    state_changed = pyqtSignal()

    def __init__(self, filename, suffix, outlines_only=False, default_color='red'):
        super().__init__()

        self.outlines_only = outlines_only

        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        self.load_frame(filename)

        self.checkbox = QCheckBox()
        if self.outlines_only and False:
            self.checkbox.setChecked(True)
        else:
            self.checkbox.setChecked(False)
        self.checkbox.stateChanged.connect(self.state_changed.emit)
        self.main_layout.addWidget(self.checkbox)

        self.colorpicker = ColorPickerPushButton(default_color, suffix)
        self.colorpicker.color_changed.connect(self.state_changed.emit)
        self.main_layout.addWidget(self.colorpicker)

        if not self.outlines_only:
            self.spinbox = QDoubleSpinBox()
            self.spinbox.setMinimum(0.0)
            self.spinbox.setMaximum(1.0)
            self.spinbox.setValue(1.0)
            self.spinbox.setSingleStep(0.1)
        else:
            self.spinbox = QSpinBox()
            self.spinbox.setMinimum(0)
            self.spinbox.setMaximum(100)
            self.spinbox.setSingleStep(1)
            self.spinbox.setValue(15)
        self.spinbox.valueChanged.connect(self.state_changed.emit)
        self.main_layout.addWidget(self.spinbox)

    def load_frame(self, filename):
        self.frame = Frame(filename)
        if self.outlines_only:
            self.bodies, self.holes = self.frame.get_contours()

    def get_label(self):
        return self.colorpicker.text()

    def get_color(self):
        return (
            self.colorpicker.color.red(),
            self.colorpicker.color.green(),
            self.colorpicker.color.blue(),
        )
    
    def get_alpha(self):
        if not self.outlines_only:
            return self.spinbox.value()
        else:
            return 1.0
    
    def get_linewidth(self):
        if self.outlines_only:
            return self.spinbox.value()
        else:
            return None

    def get_enabled(self):
        return self.checkbox.isChecked()
    
