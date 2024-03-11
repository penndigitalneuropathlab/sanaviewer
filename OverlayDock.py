
import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QLabel, QCheckBox, QHBoxLayout, QVBoxLayout, QDockWidget, QDoubleSpinBox, QSpinBox

from ColorPicker import ColorPickerPushButton

from sana.image import Frame, create_mask

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

        self.entry_widgets = []

        self.entry_layout = QVBoxLayout()

        self.setLayout(self.entry_layout)

    def set_overlay_entries(self, d):

        # clear the widgets
        for widget in self.entry_widgets:
            self.entry_layout.removeWidget(widget)
            # TODO: delete widget?
        self.entry_widgets = []

        # find main masks if available
        for f in os.listdir(d):
            if '_MAIN_' in f and not '_DEFORM_' in f and f.endswith('.dat.npz'):
                widget = OverlayEntryWidget(os.path.join(d, f), 'MAIN_ROI', outlines_only=True, default_color='black')
                self.entry_layout.addWidget(widget)
                self.entry_widgets.append(widget)

        # find the files
        overlay_files = []
        for f in os.listdir(d):
            if f.endswith('.dat.npz'):
                for suffix in self.VALID_SUFFIXES:
                    if suffix in f:
                        overlay_files.append((suffix, f))
                        break
            
        # create the widgets
        for suffix, f in overlay_files:
            widget = OverlayEntryWidget(os.path.join(d, f), suffix)
            self.entry_layout.addWidget(widget)
            self.entry_widgets.append(widget)

class OverlayEntryWidget(QWidget):
    state_changed = pyqtSignal()

    def __init__(self, filename, suffix, outlines_only=False, default_color='red'):
        super().__init__()

        self.outlines_only = outlines_only

        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        self.frame = Frame(filename)
        if self.outlines_only:
            self.main_roi_bodies, self.main_roi_holes = self.frame.get_contours()

        self.checkbox = QCheckBox()
        if self.outlines_only:
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
            self.spinbox.setValue(5)
        self.spinbox.valueChanged.connect(self.state_changed.emit)
        self.main_layout.addWidget(self.spinbox)

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
    
