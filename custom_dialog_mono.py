import sys
import librosa as ls 
import numpy as np

from singleton import Database
from main_processing import MainProcessing
from PyQt5.QtCore import Qt, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWidgets import (
    QDialog, 
    QDialogButtonBox, 
    QWidget, 
    QVBoxLayout, 
    QLabel, 
    QHBoxLayout, 
    QLineEdit, 
    QPushButton,
    QFileDialog,
    QMessageBox
)


class CustomDialogMono(QDialog):
    
    LB_path = pyqtSignal(str)

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setWindowTitle("Cargar Señal")

        self.setMinimumWidth(600)
        
        self.layout_vertical = QVBoxLayout()
        self.layout_horizontal = QHBoxLayout()
        self.layout_vertical_channel = QVBoxLayout()
        self.layout_vertical_path = QVBoxLayout()
        self.layout_vertical_button = QVBoxLayout()

        self.canal_LB = QLabel("Señal")

        self.layout_vertical_channel.addWidget(self.canal_LB)

        self.canal_LB_path = QLineEdit()

        self.layout_vertical_path.addWidget(self.canal_LB_path)

        self.canal_LB_button = QPushButton("Open")
        self.canal_LB_button.pressed.connect(self.LB_open)
        self.LB_path.connect(self.canal_LB_path.setText)
        
        self.layout_vertical_button.addWidget(self.canal_LB_button)

        self.layout_horizontal.addLayout(self.layout_vertical_channel)
        self.layout_horizontal.addLayout(self.layout_vertical_path)
        self.layout_horizontal.addLayout(self.layout_vertical_button)

        self.layout_vertical.addLayout(self.layout_horizontal)
        self.setLayout(self.layout_vertical)
        
        self.process_button = QPushButton("Cargar")
        self.process_button.pressed.connect(self.open_file)

        self.process_button.setMaximumWidth(200)
        self.layout_vertical.addWidget(self.process_button)
        
  
        
    #Apertura de archivos

    def LB_open(self):

        filename, _ = QFileDialog.getOpenFileName(self, 'Open File')

        if filename: 
            try: 
                self.LB_path.emit(filename)
            except:
                QMessageBox.critical(f"Could not load file: {e}")


    #Botón Procesamiento
    def open_file(self):

        path = self.canal_LB_path.text()
        ambi = []

        audio, Fs = ls.load(path, sr = None)
        ambi.append(audio)

        ambi.append(Fs)    
        audios = Database()
        audios.change(ambi)
        self.close()