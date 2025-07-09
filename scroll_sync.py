#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Synchronized Image Viewer

A PyQt5 application for viewing two images side by side with synchronized scrolling and zooming.

Usage:
    python image_viewer.py                    # Launch with empty panels
    python image_viewer.py image1.jpg        # Load image1 to left panel
    python image_viewer.py image1.jpg image2.png  # Load image1 to left, image2 to right
    
Supported formats: PNG, JPG, JPEG, BMP, GIF
"""

import sys
import os
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QDragEnterEvent, QDropEvent
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import (
    QLabel,
    QSizePolicy,
    QScrollArea,
    QMessageBox,
    QMainWindow,
    QMenu,
    QAction,
    qApp,
    QFileDialog,
    QWidget,
    QHBoxLayout,
    QApplication,
    QVBoxLayout
)


class DragDropLabel(QLabel):
    def __init__(self, parent=None, side="left"):
        super().__init__(parent)
        self.parent_widget = parent
        self.side = side
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            # Check if any of the URLs are image files
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.pdf')):
                        event.acceptProposedAction()
                        return
        event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.pdf')):

                        import os

                        file_extension = os.path.splitext(file_path)[1].lower()

                        import ipdb; ipdb.set_trace()

                        if file_extension == '.pdf':
                            self.parent_widget.loadPDF(file_path, self.side)
                        else:
                            self.parent_widget.loadImage(file_path, self.side)
                        event.acceptProposedAction()
                        return
        event.ignore()


class QImageViewSync(QWidget):
    def __init__(self, window=None):
        super().__init__()

        self.window = window
        self.printer = QPrinter()
        self.scaleFactor = 1.0
        self.pressed = False
        self.initialPosX = 0
        self.initialPosY = 0

        # Initialize left side with drag and drop
        self.imageLabelLeft = DragDropLabel(self, "left")
        self.imageLabelLeft.setBackgroundRole(QPalette.Base)
        self.imageLabelLeft.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabelLeft.setScaledContents(False)  # Changed to False for actual size
        self.imageLabelLeft.setAlignment(Qt.AlignCenter)
        self.imageLabelLeft.setMinimumSize(300, 200)
        self.imageLabelLeft.setStyleSheet("border: 2px dashed #aaa; background-color: #f9f9f9;")
        self.imageLabelLeft.setText("Left Image\n\nDrag & Drop an image here\nor use File > Open Left")

        self.scrollAreaLeft = QScrollArea()
        self.scrollAreaLeft.setBackgroundRole(QPalette.Dark)
        self.scrollAreaLeft.setWidget(self.imageLabelLeft)
        self.scrollAreaLeft.setWidgetResizable(False)  # Changed to False for actual size display
        self.scrollAreaLeft.setMinimumSize(300, 200)

        # Initialize right side with drag and drop
        self.imageLabelRight = DragDropLabel(self, "right")
        self.imageLabelRight.setBackgroundRole(QPalette.Base)
        self.imageLabelRight.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabelRight.setScaledContents(False)  # Changed to False for actual size
        self.imageLabelRight.setAlignment(Qt.AlignCenter)
        self.imageLabelRight.setMinimumSize(300, 200)
        self.imageLabelRight.setStyleSheet("border: 2px dashed #aaa; background-color: #f9f9f9;")
        self.imageLabelRight.setText("Right Image\n\nDrag & Drop an image here\nor use File > Open Right")

        self.scrollAreaRight = QScrollArea()
        self.scrollAreaRight.setBackgroundRole(QPalette.Dark)
        self.scrollAreaRight.setWidget(self.imageLabelRight)
        self.scrollAreaRight.setWidgetResizable(False)  # Changed to False for actual size display
        self.scrollAreaRight.setMinimumSize(300, 200)

        # Create layout
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.scrollAreaLeft)
        self.layout.addWidget(self.scrollAreaRight)
        self.setLayout(self.layout)

        # Connect scroll bars for synchronization
        self.scrollAreaLeft.verticalScrollBar().valueChanged.connect(
            self.scrollAreaRight.verticalScrollBar().setValue
        )
        self.scrollAreaLeft.horizontalScrollBar().valueChanged.connect(
            self.scrollAreaRight.horizontalScrollBar().setValue
        )
        self.scrollAreaRight.verticalScrollBar().valueChanged.connect(
            self.scrollAreaLeft.verticalScrollBar().setValue
        )
        self.scrollAreaRight.horizontalScrollBar().valueChanged.connect(
            self.scrollAreaLeft.horizontalScrollBar().setValue
        )

        # Set up mouse events
        self.scrollAreaLeft.mouseMoveEvent = self.mouseMoveEventLeft
        self.scrollAreaLeft.mousePressEvent = self.mousePressEventLeft
        self.scrollAreaLeft.mouseReleaseEvent = self.mouseReleaseEventLeft

        self.scrollAreaRight.mouseMoveEvent = self.mouseMoveEventRight
        self.scrollAreaRight.mousePressEvent = self.mousePressEventRight
        self.scrollAreaRight.mouseReleaseEvent = self.mouseReleaseEventRight

        self.imageLabelLeft.setCursor(Qt.OpenHandCursor)
        self.imageLabelRight.setCursor(Qt.OpenHandCursor)

    def loadImage(self, file_path, side):
        """Load an image into the specified side (left, right, or both)"""
        print(f"Loading {side}: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self, "Image Viewer", f"File not found: {file_path}"
            )
            return False
        
        # Check file extension
        if not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            QMessageBox.warning(
                self, "Image Viewer", f"Unsupported file format: {file_path}"
            )
            return False
        
        image = QImage(file_path)
        if image.isNull():
            QMessageBox.information(
                self, "Image Viewer", f"Cannot load {file_path}"
            )
            return False

        pixmap = QPixmap.fromImage(image)
        
        if side == "left" or side == "both":
            self.imageLabelLeft.setPixmap(pixmap)
            self.imageLabelLeft.setStyleSheet("border: 1px solid #333;")
            # Set the label size to match the image size for actual size display
            self.imageLabelLeft.adjustSize()
            if self.window:
                self.window.printLeftAct.setEnabled(True)
        
        if side == "right" or side == "both":
            self.imageLabelRight.setPixmap(pixmap)
            self.imageLabelRight.setStyleSheet("border: 1px solid #333;")
            # Set the label size to match the image size for actual size display
            self.imageLabelRight.adjustSize()
            if self.window:
                self.window.printRightAct.setEnabled(True)
        
        self.scaleFactor = 1.0
        
        if self.window:
            self.window.fitToWindowAct.setEnabled(True)
            self.updateActions()
        
        return True

    def mousePressEventLeft(self, event):
        self.pressed = True
        self.imageLabelLeft.setCursor(Qt.ClosedHandCursor)
        self.initialPosX = (
            self.scrollAreaLeft.horizontalScrollBar().value() + event.pos().x()
        )
        self.initialPosY = (
            self.scrollAreaLeft.verticalScrollBar().value() + event.pos().y()
        )

    def mouseReleaseEventLeft(self, event):
        self.pressed = False
        self.imageLabelLeft.setCursor(Qt.OpenHandCursor)
        self.initialPosX = self.scrollAreaLeft.horizontalScrollBar().value()
        self.initialPosY = self.scrollAreaLeft.verticalScrollBar().value()

    def mouseMoveEventLeft(self, event):
        if self.pressed:
            self.scrollAreaLeft.horizontalScrollBar().setValue(
                self.initialPosX - event.pos().x()
            )
            self.scrollAreaLeft.verticalScrollBar().setValue(
                self.initialPosY - event.pos().y()
            )

    def mousePressEventRight(self, event):
        self.pressed = True
        self.imageLabelRight.setCursor(Qt.ClosedHandCursor)
        self.initialPosX = (
            self.scrollAreaRight.horizontalScrollBar().value() + event.pos().x()
        )
        self.initialPosY = (
            self.scrollAreaRight.verticalScrollBar().value() + event.pos().y()
        )

    def mouseReleaseEventRight(self, event):
        self.pressed = False
        self.imageLabelRight.setCursor(Qt.OpenHandCursor)
        self.initialPosX = self.scrollAreaRight.horizontalScrollBar().value()
        self.initialPosY = self.scrollAreaRight.verticalScrollBar().value()

    def mouseMoveEventRight(self, event):
        if self.pressed:
            self.scrollAreaRight.horizontalScrollBar().setValue(
                self.initialPosX - event.pos().x()
            )
            self.scrollAreaRight.verticalScrollBar().setValue(
                self.initialPosY - event.pos().y()
            )

    def open(self):
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image File",
            "",
            "Images (*.png *.jpeg *.jpg *.bmp *.gif);;All Files (*)",
            options=QFileDialog.DontUseNativeDialog if hasattr(QFileDialog, 'DontUseNativeDialog') else QFileDialog.Options()
        )
        if fileName:
            self.loadImage(fileName, "both")

    def openLeft(self):
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "Open Left Image",
            "",
            "Images (*.png *.jpeg *.jpg *.bmp *.gif);;All Files (*)",
            options=QFileDialog.DontUseNativeDialog if hasattr(QFileDialog, 'DontUseNativeDialog') else QFileDialog.Options()
        )
        if fileName:
            self.loadImage(fileName, "left")

    def openRight(self):
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "Open Right Image",
            "",
            "Images (*.png *.jpeg *.jpg *.bmp *.gif);;All Files (*)",
            options=QFileDialog.DontUseNativeDialog if hasattr(QFileDialog, 'DontUseNativeDialog') else QFileDialog.Options()
        )
        if fileName:
            self.loadImage(fileName, "right")

    def printLeft(self):
        if not self.imageLabelLeft.pixmap():
            return
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabelLeft.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabelLeft.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabelLeft.pixmap())

    def printRight(self):
        if not self.imageLabelRight.pixmap():
            return
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabelRight.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabelRight.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabelRight.pixmap())

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabelLeft.adjustSize()
        self.imageLabelRight.adjustSize()
        self.scaleFactor = 1.0

    def about(self):
        QMessageBox.about(
            self,
            "Synchronized Image Viewer",
            "<p>The <b>Synchronized Image Viewer</b> allows you to view two images "
            "side by side with synchronized scrolling and zooming.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>Load different images in left and right panels</li>"
            "<li>Synchronized scrolling between panels</li>"
            "<li>Zoom in/out functionality</li>"
            "<li>Print support for both images</li>"
            "<li>Fit to window mode (optional)</li>"
            "<li>Images display at actual size by default</li>"
            "</ul>",
        )

    def updateActions(self):
        if self.window:
            self.window.zoomInAct.setEnabled(not self.window.fitToWindowAct.isChecked())
            self.window.zoomOutAct.setEnabled(not self.window.fitToWindowAct.isChecked())
            self.window.normalSizeAct.setEnabled(not self.window.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        
        if self.imageLabelLeft.pixmap():
            self.imageLabelLeft.resize(
                self.scaleFactor * self.imageLabelLeft.pixmap().size()
            )
        if self.imageLabelRight.pixmap():
            self.imageLabelRight.resize(
                self.scaleFactor * self.imageLabelRight.pixmap().size()
            )

        self.adjustScrollBar(self.scrollAreaLeft.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollAreaLeft.verticalScrollBar(), factor)
        self.adjustScrollBar(self.scrollAreaRight.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollAreaRight.verticalScrollBar(), factor)

        if self.window:
            self.window.zoomInAct.setEnabled(self.scaleFactor < 3.0)
            self.window.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(
            int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep() / 2))
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.imageViewSync = QImageViewSync(window=self)
        self.setCentralWidget(self.imageViewSync)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Synchronized Image Viewer")
        self.resize(1200, 600)
        
        # Ensure window is visible
        self.show()

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.imageViewSync.scrollAreaLeft.setWidgetResizable(fitToWindow)
        self.imageViewSync.scrollAreaRight.setWidgetResizable(fitToWindow)
        
        # Update scaled contents property based on fit to window state
        self.imageViewSync.imageLabelLeft.setScaledContents(fitToWindow)
        self.imageViewSync.imageLabelRight.setScaledContents(fitToWindow)
        
        if not fitToWindow:
            self.imageViewSync.normalSize()

        self.imageViewSync.updateActions()

    def createActions(self):
        self.openLeftAct = QAction(
            "&Open Left...", self, shortcut="Ctrl+O", triggered=self.imageViewSync.openLeft
        )
        self.openRightAct = QAction(
            "&Open Right...", self, shortcut="Shift+Ctrl+O", triggered=self.imageViewSync.openRight
        )
        self.printLeftAct = QAction(
            "&Print Left...",
            self,
            shortcut="Ctrl+P",
            enabled=False,
            triggered=self.imageViewSync.printLeft,
        )
        self.printRightAct = QAction(
            "&Print Right...",
            self,
            shortcut="Shift+Ctrl+P",
            enabled=False,
            triggered=self.imageViewSync.printRight,
        )
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        
        self.zoomInAct = QAction(
            "Zoom &In (25%)",
            self,
            shortcut="Ctrl++",
            enabled=False,
            triggered=self.imageViewSync.zoomIn,
        )
        self.zoomOutAct = QAction(
            "Zoom &Out (25%)",
            self,
            shortcut="Ctrl+-",
            enabled=False,
            triggered=self.imageViewSync.zoomOut,
        )
        self.normalSizeAct = QAction(
            "&Normal Size",
            self,
            shortcut="Ctrl+0",
            enabled=False,
            triggered=self.imageViewSync.normalSize,
        )
        self.fitToWindowAct = QAction(
            "&Fit to Window",
            self,
            enabled=False,
            checkable=True,
            shortcut="Ctrl+F",
            triggered=self.fitToWindow,
        )
        self.aboutAct = QAction("&About", self, triggered=self.imageViewSync.about)
        self.aboutQtAct = QAction("About &Qt", self, triggered=qApp.aboutQt)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openLeftAct)
        self.fileMenu.addAction(self.openRightAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.printLeftAct)
        self.fileMenu.addAction(self.printRightAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)


def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Synchronized Image Viewer")
    app.setOrganizationName("ImageViewer")
    
    # Create and show main window
    window = MainWindow()
    
    # Handle command line arguments for loading images
    args = sys.argv[1:]  # Skip the script name
    if len(args) >= 1:
        # Load first image to left panel
        left_image = args[0]
        if left_image and left_image.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            try:
                window.imageViewSync.loadImage(left_image, "left")
                print(f"Loaded left image: {left_image}")
            except Exception as e:
                print(f"Error loading left image '{left_image}': {e}")
        else:
            print(f"Invalid image format for left image: {left_image}")
    
    if len(args) >= 2:
        # Load second image to right panel
        right_image = args[1]
        if right_image and right_image.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            try:
                window.imageViewSync.loadImage(right_image, "right")
                print(f"Loaded right image: {right_image}")
            except Exception as e:
                print(f"Error loading right image '{right_image}': {e}")
        else:
            print(f"Invalid image format for right image: {right_image}")
    
    if len(args) > 2:
        print("Warning: Only the first two image arguments will be used.")
    
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()