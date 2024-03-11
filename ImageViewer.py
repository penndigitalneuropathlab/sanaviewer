#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import time

import cv2
import numpy as np
from sana.image import Frame, overlay_mask
from PIL import Image
from PIL.ImageQt import ImageQt

from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF
from PyQt6.QtGui import QImage, QPixmap, QPalette, QPainter, QGuiApplication, QTransform, QAction, QMouseEvent
from PyQt6.QtWidgets import QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QFileDialog, QStyle, QToolBar, QPushButton, QDockWidget, QDial, QLineEdit, QWidget, QVBoxLayout, QSpinBox, QApplication

from ColorDeconvolutionDock import ColorDeconvolutionDockWidget
from OverlayDock import OverlayDockWidget

# from RotationDial import RotationDialWidget

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # TODO: this might be off by a pixel?
        self.SCROLLBAR_EXTENT = QApplication.style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent)
        # self.SCROLLBAR_WIDTH = self.SCROLLBAR_EXTENT + self.scroll_area.width() - self.scrollAreaWidgetContents.width()
        # self.SCROLLBAR_EXTENT += self.scroll_area.width() - ui->scrollAreaWidgetContents->width();
        self.TITLEBAR_HEIGHT = QApplication.style().pixelMetric(QStyle.PixelMetric.PM_TitleBarHeight)

        self.DESKTOP_RECT = QApplication.primaryScreen().availableGeometry()
        self.DESKTOP_HEIGHT = self.DESKTOP_RECT.height()
        self.DESKTOP_WIDTH = self.DESKTOP_RECT.width()

        self.scale_factor = 1.0
        self.rotation_angle = 0

        self.image_label = QLabel()
        self.image_label.setBackgroundRole(QPalette.ColorRole.Base)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.image_label.setScaledContents(True)

        self.scroll_area = QScrollArea()
        # self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setVisible(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)

        self.setCentralWidget(self.scroll_area)

        # toolbars
        self.create_navigation_toolbar()

        # docks
        self.create_rotation_dock()
        self.create_deconvolution_dock()
        self.create_overlay_dock()

        # actions
        self.create_actions()

        # menus
        self.create_menus()

        self.setWindowTitle("Image Viewer")
        self.resize(800, 600)

        self.open_frame('./data/2002-070-35F_R_MFC_SMI94_400_09-08-21_EX/GM_MFCcrown/2002-070-35F_R_MFC_SMI94_400_09-08-21_EX_ORIG.png')

    def set_viewer_size(self, size):
        self.resize(size)

    def open_frame(self, file_name=""):
        if file_name == "" or file_name == False:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                    'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        if file_name:
            if not os.path.exists(file_name):
                QMessageBox.information(self, "Image Viewer", "File does not exist: %s" % file_name)
                return
            try:
                frame = Frame(file_name)
                image_array = frame.img
                # image_array = np.asarray(Image.open(file_name))
            except:
                QMessageBox.information(self, "Image Viewer", "Cannot load %s" % file_name)
                return

        # parse the data storage structure
        self.file_name = file_name
        self.roi_directory, _ = os.path.split(self.file_name)
        self.slide_directory, self.roi_name = os.path.split(self.roi_directory)
        self.data_directory, self.slide_name = os.path.split(self.slide_directory)

        # update the necessary widgets
        self.set_source_image(image_array)

        # update toolbars
        self.update_navigation_toolbar()

        # update docks
        self.update_rotation_dock()
        self.update_deconvolution_dock()
        self.update_overlay_dock()

    def get_directories(self, d):
        return sorted([x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x))])

    def get_next_frame(self):

        # find the next roi in the slide directory
        roi_names = self.get_directories(self.slide_directory)
        next_roi_name_idx = roi_names.index(self.roi_name) + 1
        if next_roi_name_idx < len(roi_names):
            next_slide_name = self.slide_name
            next_roi_name = roi_names[next_roi_name_idx]
        
        # find the first roi in the next slide
        else:
            slide_names = self.get_directories(self.data_directory)

            # look forward through the slides
            i = 1
            while True:

                # get the next slide
                next_slide_name_idx = slide_names.index(self.slide_name) + i
                if next_slide_name_idx < len(slide_names):
                    next_slide_name = slide_names[next_slide_name_idx]
                    next_slide_directory = os.path.join(self.data_directory, next_slide_name)

                    # get the first roi in this new slide
                    roi_names = self.get_directories(next_slide_directory)
                    if len(roi_names) != 0:
                        next_roi_name = roi_names[0]
                        break

                    # slide is empty, continue to next slide
                    else:
                        i += 1

                # no more slides and rois to look for
                else:
                    next_slide_name = ""
                    next_roi_name = ""
                    break

        return next_slide_name, next_roi_name
                
    def get_previous_frame(self):

        # find the previous roi in the slide directory
        roi_names = self.get_directories(self.slide_directory)
        previous_roi_name_idx = roi_names.index(self.roi_name) - 1
        if previous_roi_name_idx >= 0:
            previous_slide_name = self.slide_name
            previous_roi_name = roi_names[previous_roi_name_idx]
    
        # find the last roi in the previous slide
        else:
            slide_names = self.get_directories(self.data_directory)

            # look backward through the slides
            i = 1
            while True:

                # get the previous slide
                previous_slide_name_idx = slide_names.index(self.slide_name) - i
                if previous_slide_name_idx >= 0:
                    previous_slide_name = slide_names[previous_slide_name_idx]
                    previous_slide_directory = os.path.join(self.data_directory, previous_slide_name)

                    # get the last roi in this new slide
                    roi_names = self.get_directories(previous_slide_directory)
                    if len(roi_names) != 0:
                        previous_roi_name = roi_names[-1]
                        break

                    # slide is empty, continue to previous slide
                    else:
                        i -= 1

                # no more slides and rois to look for
                else:
                    previous_slide_name = ""
                    previous_roi_name = ""
                    break

        return previous_slide_name, previous_roi_name

    def open_previous_frame(self):
        if self.previous_roi_name != "":
            file_name = os.path.join(self.data_directory, self.previous_slide_name, self.previous_roi_name, self.previous_slide_name+'_ORIG.png')
            self.open_frame(file_name)

    def open_next_frame(self):
        if self.next_roi_name != "":
            file_name = os.path.join(self.data_directory, self.next_slide_name, self.next_roi_name, self.next_slide_name+'_ORIG.png')
            self.open_frame(file_name)      
                 
    def set_source_image(self, image_array: np.ndarray):
        self.source_image_array = image_array

        self.source_image = QImage(
            self.source_image_array, 
            self.source_image_array.shape[1], 
            self.source_image_array.shape[0],
            self.source_image_array.strides[0],
            QImage.Format.Format_RGB888
        )

        # calculate aspect ratio of the source image
        self.aspect_ratio = self.source_image.height() / self.source_image.width()

        deconvolution_image_array = self.deconvolve_image(self.source_image_array)

        # initialize the window with the source image
        self.set_deconvolved_image(deconvolution_image_array)

    def set_deconvolved_image(self, image_array: np.ndarray):
        self.deconvolved_image_array = image_array

        self.deconvolved_image = QImage(
            self.deconvolved_image_array, 
            self.deconvolved_image_array.shape[1], 
            self.deconvolved_image_array.shape[0],
            self.deconvolved_image_array.strides[0],
            QImage.Format.Format_RGB888,     
        )

        overlay_image_array = self.overlay_masks(self.deconvolved_image_array)

        self.set_overlay_image(overlay_image_array)

    def set_overlay_image(self, image_array: np.ndarray):
        self.overlay_image_array = image_array

        self.overlay_image = QImage(
            self.overlay_image_array, 
            self.overlay_image_array.shape[1], 
            self.overlay_image_array.shape[0],
            self.overlay_image_array.strides[0],
            QImage.Format.Format_RGB888,     
        )

        rotated_image_array = self.rotate_image(self.overlay_image_array, self.rotation_angle)

        self.set_rotated_image(rotated_image_array)

    def set_rotated_image(self, image_array: np.ndarray):
        self.rotated_image_array = image_array      

        self.rotated_image = QImage(
            self.rotated_image_array, 
            self.rotated_image_array.shape[1], 
            self.rotated_image_array.shape[0],
            self.rotated_image_array.strides[0],
            QImage.Format.Format_RGB888
        )

        self.rotated_aspect_ratio = self.rotated_image.height() / self.rotated_image.width()

        rescaled_image_array = self.rescale_image(self.rotated_image_array, self.scale_factor)

        self.set_rescaled_image(rescaled_image_array)

    def set_rescaled_image(self, image_array: np.ndarray):
        self.rescaled_image_array = image_array

        self.rescaled_image = QImage(
            self.rescaled_image_array, 
            self.rescaled_image_array.shape[1], 
            self.rescaled_image_array.shape[0],
            self.rescaled_image_array.strides[0],
            QImage.Format.Format_RGB888,
        )
        self.set_current_image(self.rescaled_image_array)

    def set_current_image(self, image_array: np.ndarray):
        self.current_image_array = image_array

        self.current_image = QImage(
            self.current_image_array, 
            self.current_image_array.shape[1], 
            self.current_image_array.shape[0],
            self.current_image_array.strides[0],
            QImage.Format.Format_RGB888
        )

        self.current_pixmap = QPixmap.fromImage(self.current_image)
        self.image_label.setPixmap(self.current_pixmap)

        # show the scroll area if needed
        self.scroll_area.setVisible(True)

        # update the size of the image label
        self.image_label.adjustSize()

    def rescale_image(self, image_array: np.ndarray, scale_factor: float):
        h = int(round(scale_factor * image_array.shape[0]))
        w = int(round(scale_factor * image_array.shape[1]))
        rescaled_image_array = cv2.resize(image_array, dsize=(w, h), interpolation=cv2.INTER_CUBIC)

        return rescaled_image_array

    def rotate_image(self, image_array: np.ndarray, angle: int):

        # get horz,vert scroll bar coord

        # convert to coord on the image

        frame = Frame(image_array)
        M, new_w, new_h = frame.get_rotation_matrix(-angle)
        frame.warp_affine(M, new_w, new_h)
        rotated_image_array = frame.img

        # transform coord using M

        # convert back to horz/vert scroll bar values and set them <- result, rotate around viewer center

        return rotated_image_array

    def deconvolve_image(self, image_array: np.ndarray):
        if all([self.stain_A_enabled,self.stain_B_enabled,self.stain_C_enabled]):
            return image_array
        
        stains = self.deconvolution_dock.widget.ss.separate(image_array)

        if self.stain_A_enabled:
            stains[:,:,0] = np.clip(stains[:,:,0], self.stain_A_range[0], self.stain_A_range[1])
        else:
            stains[:,:,0] = 0
        if self.stain_B_enabled:
            stains[:,:,1] = np.clip(stains[:,:,1], self.stain_B_range[0], self.stain_B_range[1])
        else:
            stains[:,:,1] = 0
        if self.stain_C_enabled:
            stains[:,:,2] = np.clip(stains[:,:,2], self.stain_C_range[0], self.stain_C_range[1])
        else:
            stains[:,:,2] = 0
        deconvolved_image_array = self.deconvolution_dock.widget.ss.combine(stains)

        return deconvolved_image_array

    def overlay_masks(self, image_array: np.ndarray):
        overlay_frame = Frame(image_array)
        
        for widget in self.overlay_dock.widget.entry_widgets:
            if widget.get_enabled():
                if widget.outlines_only:
                    overlay_frame = overlay_mask(
                        overlay_frame, None,
                        main_roi=widget.main_roi_bodies[0].polygon,
                        alpha=widget.get_alpha(),
                        color=widget.get_color(),
                        linewidth=widget.get_linewidth(),
                    )
                else:
                    overlay_frame = overlay_mask(
                        overlay_frame, widget.frame, 
                        alpha=widget.get_alpha(), 
                        color=widget.get_color(),
                    )

        overlay_image_array = overlay_frame.img

        return overlay_image_array

    def save_frame(self, file_name=""):
        if file_name == "" or file_name == False:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, 'QFileDialog.getSaveFileName()', '',
                                                    'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        if file_name:
            
            # calculate the visible rect of the image
            x = self.scroll_area.horizontalScrollBar().value()
            y = self.scroll_area.verticalScrollBar().value()
            w = self.width()
            h = self.height()
            if self.vertical_scroll_bar_is_visible():
                w -= self.SCROLLBAR_EXTENT
            if self.horizontal_scroll_bar_is_visible():
                h -= self.SCROLLBAR_EXTENT
            if self.navigation_toolbar.isVisible():
                h -= self.navigation_toolbar.height()

            # extract the rect from the current image        
            rect = QRect(x, y, w, h)
            save_image = self.current_image.copy(rect)

            # save the image
            save_image.save(file_name)

    def set_scale_factor(self, scale_factor):
        self.scale_factor = scale_factor

        rescaled_image_array = self.rescale_image(self.rotated_image_array, self.scale_factor)

        self.set_rescaled_image(rescaled_image_array)

    # update the scale factor by 25%, update the scroll bar values so that they do not move
    def zoom_in(self):
        self.set_scale_factor(self.scale_factor * 1.25)
        self.update_scroll_bars(1.25)
        if max([self.current_image.width(), self.current_image.height()]) > 10000:
            self.zoom_in_action.setDisabled(True)
        else:
            self.zoom_in_action.setEnabled(True)
        self.zoom_out_action.setEnabled(True)
    def zoom_out(self):
        self.set_scale_factor(self.scale_factor / 1.25)
        self.update_scroll_bars(1/1.25)
        if min([self.current_image.width(), self.current_image.height()]) < 100:
            self.zoom_out_action.setDisabled(True)
        else:
            self.zoom_out_action.setEnabled(True)
        self.zoom_in_action.setEnabled(True)
    def reset_zoom(self):
        self.set_scale_factor(1.0)
        self.zoom_in_action.setEnabled(True)
        self.zoom_in_action.setEnabled(True)

    # maximize the image such that the entire image fits on the desktop
    def maximize(self):

        # fit image to desktop, using the height or width of desktop as the limiter based on the aspect ratio
        if self.rotated_aspect_ratio > 1:

            # calculate the available height
            h = self.DESKTOP_HEIGHT
            h -= self.TITLEBAR_HEIGHT
            if self.navigation_toolbar.isVisible():
                h -= self.navigation_toolbar.height()
            # if self.scroll_area.horizontalScrollBar().isVisible():
            #     h -= self.SCROLLBAR_EXTENT

            # calculate the amount to zoom based on the available desktop height
            self.set_scale_factor(h / self.rotated_image.height())

            # top left corner to move the window to center it
            px = self.DESKTOP_RECT.width()//2 - self.current_image.width()//2
            py = 0

            screen_h = self.DESKTOP_HEIGHT - self.TITLEBAR_HEIGHT
            screen_w = self.current_image.width()
            if self.rotation_dock.isVisible() and not self.rotation_dock.isFloating():
                screen_w += self.rotation_dock.width()
        
        else:

            # calculate the available width
            w = self.DESKTOP_WIDTH
            if self.rotation_dock.isVisible() and not self.rotation_dock.isFloating():
                w -= self.rotation_dock.width()
            # if self.scroll_area.verticalScrollBar().isVisible():
            #     w -= self.SCROLLBAR_EXTENT

            # calculate the amount to zoom based on the available desktop width
            self.set_scale_factor(w / self.rotated_image.width())

            # top left corner to move the window to center it
            px = 0
            py = self.DESKTOP_RECT.height()//2 - self.current_image.height()//2

            screen_h = self.current_image.height() + self.navigation_toolbar.height()
            screen_w = self.DESKTOP_WIDTH

        # center the window on the screen
        self.move(QPoint(px, py))

        # resize the window to the image size
        self.resize(screen_w, screen_h)

    # when the factor changes, need to move the scroll bars as well
    def update_scroll_bars(self, factor):
        self.update_scroll_bar(self.scroll_area.horizontalScrollBar(), factor)
        self.update_scroll_bar(self.scroll_area.verticalScrollBar(), factor)
    def update_scroll_bar(self, scroll_bar, factor):
        scroll_bar.setValue(int(factor * scroll_bar.value()
                               + ((factor - 1) * scroll_bar.pageStep() / 2)))
        

    def set_image_rotation(self, angle):
        self.rotation_angle = angle - 180
        
        rotated_image_array = self.rotate_image(self.overlay_image_array, self.rotation_angle)

        self.set_rotated_image(rotated_image_array)

    def set_default_image_rotation(self):
        self.rotation_dial.setValue(180)

    # functions which see if the image dimensions surpass the MainWindow dimensions
    def horizontal_scroll_bar_is_visible(self):
        return self.current_image.size().width() > self.width()
    def vertical_scroll_bar_is_visible(self):
        return self.current_image.size().height() > self.height()

    def about(self):
        QMessageBox.about(self, "About Image Viewer",
                          "<p>The <b>Image Viewer</b> example shows how to combine "
                          "QLabel and QScrollArea to display an image. QLabel is "
                          "typically used for displaying text, but it can also display "
                          "an image. QScrollArea provides a scrolling view around "
                          "another widget. If the child widget exceeds the size of the "
                          "frame, QScrollArea automatically provides scroll bars.</p>"
                          "<p>The example demonstrates how QLabel's ability to scale "
                          "its contents (QLabel.scaledContents), and QScrollArea's "
                          "ability to automatically resize its contents "
                          "(QScrollArea.widgetResizable), can be used to implement "
                          "zooming and scaling features.</p>")

    def create_actions(self):
        self.open_action = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open_frame)
        self.save_action = QAction("&Save...", self, shortcut="Ctrl+S", triggered=self.save_frame)
        self.exit_action = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.zoom_in_action = QAction("Zoom &In (25%)", self, shortcut="Ctrl++", triggered=self.zoom_in)
        self.zoom_out_action = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+-", triggered=self.zoom_out)
        self.reset_zoom_action = QAction("&Reset Zoom", self, shortcut="Ctrl+0", triggered=self.reset_zoom)
        self.maximize_action = QAction("&Maximize", self, shortcut="Ctrl+F", triggered=self.maximize)
        self.about_action = QAction("&About", self, triggered=self.about)
        self.about_qt_action = QAction("About &Qt", self, triggered=QApplication.aboutQt)

    def create_menus(self):
        self.file_menu = QMenu("&File", self)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        self.view_menu = QMenu("&View", self)
        self.view_menu.addAction(self.rotation_dock.toggleViewAction())
        self.view_menu.addAction(self.deconvolution_dock.toggleViewAction())
        self.view_menu.addAction(self.overlay_dock.toggleViewAction())

        self.window_menu = QMenu("&Window", self)
        self.window_menu.addAction(self.zoom_in_action)
        self.window_menu.addAction(self.zoom_out_action)
        self.window_menu.addAction(self.reset_zoom_action)
        self.window_menu.addAction(self.maximize_action)

        self.help_menu = QMenu("&Help", self)
        self.help_menu.addAction(self.about_action)
        self.help_menu.addAction(self.about_qt_action)

        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.view_menu)
        self.menuBar().addMenu(self.window_menu)
        self.menuBar().addMenu(self.help_menu)

    def create_navigation_toolbar(self):
        self.navigation_toolbar = QToolBar("Frame Navigation")
        self.navigation_toolbar.hide()
        self.navigation_toolbar.setFloatable(False)
        self.navigation_toolbar.setMovable(False)
        self.addToolBar(self.navigation_toolbar)

        self.previous_button = QPushButton("")
        self.previous_button.pressed.connect(self.open_previous_frame)
        self.navigation_toolbar.addWidget(self.previous_button)

        self.current_label = QLabel("")
        self.current_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        self.navigation_toolbar.addWidget(self.current_label)

        self.next_button = QPushButton("")
        self.next_button.pressed.connect(self.open_next_frame)
        self.navigation_toolbar.addWidget(self.next_button)

    def update_navigation_toolbar(self):

        # get the previous and next roi in the dataset
        self.previous_slide_name, self.previous_roi_name = self.get_previous_frame()
        self.next_slide_name, self.next_roi_name = self.get_next_frame()

        if self.previous_roi_name != "":
            self.previous_button.setText(f'{self.previous_slide_name}\n{self.previous_roi_name}')
            self.previous_button.setEnabled(True)
        else:
            self.previous_button.setText("End of\nDataset")
            self.previous_button.setEnabled(False)

        self.current_label.setText(f'{self.slide_name}\n{self.roi_name}')
        
        if self.next_roi_name != "":
            self.next_button.setText(f'{self.next_slide_name}\n{self.next_roi_name}')
            self.next_button.setEnabled(True)
        else:
            self.next_button.setText("End of\nDataset")
            self.next_button.setEnabled(False)

        self.navigation_toolbar.show()

    def create_rotation_dock(self):
        self.rotation_dock = QDockWidget("Rotation Dock")
        self.rotation_dock.hide()
        self.rotation_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.rotation_dock)

        self.rotation_dial = QDial()
        self.rotation_dial.setWrapping(True)
        self.rotation_dial.setNotchesVisible(True)
        self.rotation_dial.setMinimum(0)
        self.rotation_dial.setMaximum(360)
        self.rotation_dial.setValue(180)
        self.rotation_dial.valueChanged.connect(self.set_image_rotation)
        self.rotation_dial.mousePressEvent = self.rotation_dial_mouse_press_event
        # TODO: double click reset rotation, or view shortcut!!
        self.rotation_dock.setWidget(self.rotation_dial)

    def update_rotation_dock(self):
        self.rotation_dock.show()

    def create_deconvolution_dock(self):
        self.deconvolution_dock = ColorDeconvolutionDockWidget("Color Deconvolution Dock")
        self.deconvolution_dock.hide()
        self.deconvolution_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.deconvolution_dock)

        self.deconvolution_dock.widget.stain_A_slider.valueChanged.connect(self.set_stain_A_range)
        self.deconvolution_dock.widget.stain_B_slider.valueChanged.connect(self.set_stain_B_range)
        self.deconvolution_dock.widget.stain_C_slider.valueChanged.connect(self.set_stain_C_range)
        self.deconvolution_dock.widget.stain_A_checkbox.stateChanged.connect(self.set_stain_A_enabled)
        self.deconvolution_dock.widget.stain_B_checkbox.stateChanged.connect(self.set_stain_B_enabled)
        self.deconvolution_dock.widget.stain_C_checkbox.stateChanged.connect(self.set_stain_C_enabled)

        self.stain_A_range = self.deconvolution_dock.widget.stain_A_slider.value()
        self.stain_B_range = self.deconvolution_dock.widget.stain_B_slider.value()
        self.stain_C_range = self.deconvolution_dock.widget.stain_C_slider.value()
        self.stain_A_enabled = self.deconvolution_dock.widget.stain_A_checkbox.isEnabled()
        self.stain_B_enabled = self.deconvolution_dock.widget.stain_B_checkbox.isEnabled()
        self.stain_C_enabled = self.deconvolution_dock.widget.stain_C_checkbox.isEnabled()

        
    def update_deconvolution_dock(self):
        self.deconvolution_dock.show()
        # TODO: update stainseparator when this is called!

    def set_stain_A_range(self, values):
        self.stain_A_range = (
            self.deconvolution_dock.widget.slider_to_od(values[0]),
            self.deconvolution_dock.widget.slider_to_od(values[1]),
        )
        self.update_deconvolution_image()
    def set_stain_B_range(self, values):
        self.stain_B_range = (
            self.deconvolution_dock.widget.slider_to_od(values[0]),
            self.deconvolution_dock.widget.slider_to_od(values[1]),
        )
        self.update_deconvolution_image()
    def set_stain_C_range(self, values):
        self.stain_C_range = (
            self.deconvolution_dock.widget.slider_to_od(values[0]),
            self.deconvolution_dock.widget.slider_to_od(values[1]),
        )
        self.update_deconvolution_image()

    def set_stain_A_enabled(self, is_enabled):
        self.stain_A_enabled = is_enabled
        self.update_deconvolution_image()
    def set_stain_B_enabled(self, is_enabled):
        self.stain_B_enabled = is_enabled
        self.update_deconvolution_image()
    def set_stain_C_enabled(self, is_enabled):
        self.stain_C_enabled = is_enabled
        self.update_deconvolution_image()

    def update_deconvolution_image(self):

        deconvolved_image_array = self.deconvolve_image(self.source_image_array)

        self.set_deconvolved_image(deconvolved_image_array)

    def create_overlay_dock(self):
        self.overlay_dock = OverlayDockWidget('Overlay Dock')
        self.overlay_dock.hide()
        self.overlay_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.overlay_dock)

    def update_overlay_dock(self):
        self.overlay_dock.widget.set_overlay_entries(self.roi_directory)
        self.overlay_dock.show()

        for widget in self.overlay_dock.widget.entry_widgets:
            widget.state_changed.connect(self.update_overlay_image)

        self.update_overlay_image()

    def update_overlay_image(self):
        overlay_image_array = self.overlay_masks(self.deconvolved_image_array)

        self.set_overlay_image(overlay_image_array)

    def rotation_dial_mouse_press_event(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self.set_default_image_rotation()
        else:
            QDial.mousePressEvent(self.rotation_dial, event)