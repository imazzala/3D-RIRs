import sys

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QImage, QTransform
from PyQt5.QtWidgets import (
    QFileDialog,
    QApplication,
    QMainWindow,
    QWidget, 
    QTabWidget,
    QDialog,
    QVBoxLayout,
    QStackedLayout,
    QLineEdit,
    QLabel,
    QDialogButtonBox,  
    QPushButton,
    QHBoxLayout,
)



class Vistas(QWidget):
    def __init__(self):
        super().__init__()
        
        hBox = QHBoxLayout()
        vBox = QVBoxLayout()
        
        self.button = QPushButton("Cargar Imagen Planta")
        self.button.setMaximumWidth(200)
        self.button.clicked.connect(self.open_file)
        hBox.addWidget(self.button)

        
        self.button_rir = QPushButton("Cargar Rir")
        self.button_rir.setMaximumWidth(200)
        self.button_rir.clicked.connect(self.open_rir)
        hBox.addWidget(self.button_rir)

        self.button_graph = QPushButton("Graficar")
        self.button_graph.setMaximumWidth(200)
        self.button_graph.clicked.connect(self.on_clicked)
        hBox.addWidget(self.button_graph)

        vBox.addLayout(hBox)

        self.label = QLabel()
        self.label.setMaximumWidth(1000)
        self.label.setMaximumHeight(800)
        
        self.rect = QRect()
        self.drag_position = QPoint()
        self.rotation = 0

        vBox.addWidget(self.label)
        self.setLayout(vBox)


    @QtCore.pyqtSlot()
    def on_clicked(self):
        if self.rect.isNull():
            self.rect = QtCore.QRect(200, 100, 350, 350)
            self.update()

    
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.rect.isNull():

            self.base_pixmap = QPixmap(self.filename).scaled(1100, 1000, Qt.KeepAspectRatio)
            
            self.overlay_pixmap = QPixmap(self.rir_filename).scaled(450, 450, Qt.KeepAspectRatio)
            self.painter = QPainter(self.base_pixmap)
            self.painter.begin(self)
            self.painter.drawPixmap(self.rect, self.overlay_pixmap)
            self.painter.setRenderHint(QtGui.QPainter.Antialiasing)
            self.painter.end()
            self.label.setPixmap(self.base_pixmap)

    
    def mousePressEvent(self, event):

        self.drag_position = event.pos() - self.rect.topLeft()
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        
        self.rect.moveTopLeft(event.pos() - self.drag_position)
        self.update()
        super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        self.drag_position = QtCore.QPoint()
        super().mouseReleaseEvent(event)    


    def mouseDoubleClickEvent(self, event):

        pixmap = self.overlay_pixmap.copy()
        self.angle = 90
        transform = QTransform().rotate(self.angle)
        self.painter.begin(self)
        pixmap = pixmap.transformed(transform, QtCore.Qt.SmoothTransformation)
        self.painter.drawPixmap(self.rect, pixmap)
        self.painter.end()
        super().mouseDoubleClickEvent(event)
        
        # angle = 90  # What angle would you like to rotate
        # self.pixmap = QPixmap("img\\label.png") # image for your label
        # pixmap_rotated = self.pixmap.transformed(QTransform().rotate(angle),QtCore.Qt.SmoothTransformation)
        # self.imageLabel.setPixmap(pixmap_rotated) 


    def open_file(self):
        self.filename, _ = QFileDialog.getOpenFileName(self, 'Open File')

    def open_rir(self):
        self.rir_filename, _ = QFileDialog.getOpenFileName(self, 'Open File')
        
    



