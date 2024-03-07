#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QGuiApplication
from PyQt5.QtWidgets import QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QAction, \
    qApp, QFileDialog, QDesktopWidget, QStyle, QToolBar, QPushButton


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # TODO: this might be off by a pixel?
        self.SCROLLBAR_EXTENT = qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        # self.SCROLLBAR_WIDTH = self.SCROLLBAR_EXTENT + self.scroll_area.width() - self.scrollAreaWidgetContents.width()
        # self.SCROLLBAR_EXTENT += self.scroll_area.width() - ui->scrollAreaWidgetContents->width();
        self.TITLEBAR_HEIGHT = qApp.style().pixelMetric(QStyle.PM_TitleBarHeight)

        self.DESKTOP_RECT = QApplication.primaryScreen().availableGeometry()
        self.DESKTOP_HEIGHT = self.DESKTOP_RECT.height()
        self.DESKTOP_WIDTH = self.DESKTOP_RECT.width()

        self.scale_factor = 1.0

        self.image_label = QLabel()
        self.image_label.setBackgroundRole(QPalette.Base)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True)

        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setVisible(False)
        self.scroll_area.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

        self.setCentralWidget(self.scroll_area)

        self.create_actions()
        self.create_menus()
        self.create_toolbars()

        self.setWindowTitle("Image Viewer")
        self.resize(800, 600)

        self.open_frame('../testing/test_segment_output/2010-011-36F_N_V1_GFAP_4K_07-13-22_PS/GM_VEC_0/2010-011-36F_N_V1_GFAP_4K_07-13-22_PS.png')

    def set_viewer_size(self, size):
        self.resize(size)

    def open_frame(self, file_name=""):
        if file_name == "" or file_name == False:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                    'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        if file_name:
            image = QImage(file_name)
            if image.isNull():
                QMessageBox.information(self, "Image Viewer", "Cannot load %s." % file_name)
                return

        # parse the data storage structure
        self.file_name = file_name
        self.roi_directory, _ = os.path.split(self.file_name)
        self.slide_directory, self.roi_name = os.path.split(self.roi_directory)
        self.data_directory, self.slide_name = os.path.split(self.slide_directory)

        # update the necessary widgets
        self.set_source_image(image)
        self.update_navigation_toolbar()

    def get_next_frame(self):

        # find the next roi in the slide directory
        roi_names = sorted(os.listdir(self.slide_directory))
        next_roi_name_idx = roi_names.index(self.roi_name) + 1
        if next_roi_name_idx < len(roi_names):
            next_slide_name = self.slide_name
            next_roi_name = roi_names[next_roi_name_idx]
        
        # find the first roi in the next slide
        else:
            slide_names = sorted(os.listdir(self.data_directory))

            # look forward through the slides
            i = 1
            while True:

                # get the next slide
                next_slide_name_idx = slide_names.index(self.slide_name) + i
                if next_slide_name_idx < len(slide_names):
                    next_slide_name = slide_names[next_slide_name_idx]
                    next_slide_directory = os.path.join(self.data_directory, next_slide_name)

                    # get the first roi in this new slide
                    roi_names = sorted(os.listdir(next_slide_directory))
                    if len(roi_names) != 0:
                        next_roi_name = roi_names[0]

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
        roi_names = sorted(os.listdir(self.slide_directory))
        previous_roi_name_idx = roi_names.index(self.roi_name) - 1
        if previous_roi_name_idx >= 0:
            previous_slide_name = self.slide_name
            previous_roi_name = roi_names[previous_roi_name_idx]
    
        # find the last roi in the previous slide
        else:
            slide_names = sorted(os.listdir(self.data_directory))

            # look backward through the slides
            i = 1
            while True:

                # get the previous slide
                previous_slide_name_idx = slide_names.index(self.slide_name) - i
                if previous_slide_name_idx >= 0:
                    previous_slide_name = slide_names[previous_slide_name_idx]
                    previous_slide_directory = os.path.join(self.data_directory, previous_slide_name)

                    # get the last roi in this new slide
                    roi_names = sorted(os.listdir(previous_slide_directory))
                    if len(roi_names) != 0:
                        previous_roi_name = roi_names[-1]
                        return previous_slide_name, previous_roi_name

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
            file_name = os.path.join(self.data_directory, self.previous_slide_name, self.previous_roi_name, self.previous_slide_name+'.png')
            self.open_frame(file_name)

    def open_next_frame(self):
        if self.next_roi_name != "":
            file_name = os.path.join(self.data_directory, self.next_slide_name, self.next_roi_name, self.next_slide_name+'.png')
            self.open_frame(file_name)      
                 
    def set_source_image(self, image: QImage):
        self.source_image = image

        # calculate aspect ratio of the source image
        self.aspect_ratio = self.source_image.height() / self.source_image.width()

        # initialize the window with the source image
        self.set_image_label(self.source_image)

    def set_image_label(self, image: QImage):
        self.current_image = image
        self.image_label.setPixmap(QPixmap.fromImage(self.current_image))

        # show the scroll area if needed
        self.scroll_area.setVisible(True)

        # update the size of the image label
        self.image_label.adjustSize()
        

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

        # rescale the image by the factor
        image = self.source_image.scaled(self.scale_factor * self.source_image.size())
        self.set_image_label(image)
        
    # update the scale factor by 25%, update the scroll bar values so that they do not move
    def zoom_in(self):
        self.set_scale_factor(self.scale_factor * 1.25)
        self.update_scroll_bars(1.25)
    def zoom_out(self):
        self.set_scale_factor(self.scale_factor / 1.25)
        self.update_scroll_bars(1/1.25)
    def normal_size(self):
        self.set_scale_factor(1.0)

    # maximize the image such that the entire image fits on the desktop
    def maximize(self):

        # fit image to desktop, using the height or width of desktop as the limiter based on the aspect ratio
        if self.aspect_ratio > 1:

            # amount to zoom, based on the desktop height minus the title bar of the MainWindow
            scale_factor = (self.DESKTOP_HEIGHT - self.TITLEBAR_HEIGHT) / self.source_image.height()
            print(self.DESKTOP_HEIGHT, self.TITLEBAR_HEIGHT, self.source_image.height())
            print(scale_factor)
            self.set_scale_factor(scale_factor)

            # scale again to account for the scroll bar is necessary
            if self.horizontal_scroll_bar_is_visible():
                scale_factor -= self.SCROLLBAR_EXTENT / self.source_image.height()
                self.set_scale_factor(scale_factor)

            # center the window on the screen
            self.move(QPoint(self.DESKTOP_RECT.center().x()-self.current_image.width()//2, 0))

        else:

            # amount to zoom, based on the desktop width
            scale_factor = self.DESKTOP_WIDTH / self.source_image.width()
            self.set_scale_factor(scale_factor)

            # scale again to account for the scroll bar is necessary
            if self.vertical_scroll_bar_is_visible():
                scale_factor -= self.SCROLLBAR_EXTENT / self.source_image.width()
                self.set_scale_factor(scale_factor)

            # center the window on the screen
            self.move(0, QPoint(self.DESKTOP_RECT.center().y()-self.current_image.height()//2))

        # resize the window to the image size
        self.resize(self.current_image.size())

    # when the factor changes, need to move the scroll bars as well
    def update_scroll_bars(self, factor):
        self.update_scroll_bar(self.scroll_area.horizontalScrollBar(), factor)
        self.update_scroll_bar(self.scroll_area.verticalScrollBar(), factor)
    def update_scroll_bar(self, scroll_bar, factor):
        scroll_bar.setValue(int(factor * scroll_bar.value()
                               + ((factor - 1) * scroll_bar.pageStep() / 2)))
        
    def update_navigation_toolbar(self):

        # get the previous and next roi in the dataset
        self.previous_slide_name, self.previous_roi_name = self.get_previous_frame()
        self.next_slide_name, self.next_roi_name = self.get_next_frame()

        if self.previous_roi_name != "":
            self.previous_button.setText(f'{self.previous_slide_name}\n{self.previous_roi_name}')
        else:
            self.previous_button.setText("End of\nDataset")
        self.current_label.setText(f'{self.slide_name}\n{self.roi_name}')
        if self.next_roi_name != "":
            self.next_button.setText(f'{self.next_slide_name}\n{self.next_roi_name}')
        else:
            self.next_button.setText("End of\nDataset")

        self.navigation_toolbar.show()

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
        self.normal_size_action = QAction("&Normal Size", self, shortcut="Ctrl+0", triggered=self.normal_size)
        self.maximize_action = QAction("&Maximize", self, shortcut="Ctrl+F", triggered=self.maximize)
        self.about_action = QAction("&About", self, triggered=self.about)
        self.about_qt_action = QAction("About &Qt", self, triggered=qApp.aboutQt)

    def create_menus(self):
        self.file_menu = QMenu("&File", self)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        self.view_menu = QMenu("&View", self)
        self.view_menu.addAction(self.zoom_in_action)
        self.view_menu.addAction(self.zoom_out_action)
        self.view_menu.addAction(self.normal_size_action)
        self.view_menu.addAction(self.maximize_action)

        self.help_menu = QMenu("&Help", self)
        self.help_menu.addAction(self.about_action)
        self.help_menu.addAction(self.about_qt_action)

        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.view_menu)
        self.menuBar().addMenu(self.help_menu)

    def create_toolbars(self):
        self.navigation_toolbar = self.addToolBar("Frame Navigation")
        self.navigation_toolbar.hide()

        self.previous_button = QPushButton("")
        self.previous_button.pressed.connect(self.open_previous_frame)
        self.navigation_toolbar.addWidget(self.previous_button)

        self.current_label = QLabel("")
        self.current_label.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.navigation_toolbar.addWidget(self.current_label)

        self.next_button = QPushButton("")
        self.next_button.pressed.connect(self.open_next_frame)
        self.navigation_toolbar.addWidget(self.next_button)

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec_())

    # TODO QScrollArea support mouse
    # base on https://github.com/baoboa/pyqt5/blob/master/examples/widgets/imageviewer.py
    #
    # if you need Two Image Synchronous Scrolling in the window by PyQt5 and Python 3
    # please visit https://gist.github.com/acbetter/e7d0c600fdc0865f4b0ee05a17b858f2