import sys
from typing import final
from PyQt5 import QtCore, QtWidgets
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import mplcursors
import os

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits import mplot3d
from custom_dialog import CustomDialog
from PyQt5.QtCore import pyqtSlot
from singleton import Database
from main_processing import MainProcessing


from custom_dialog import CustomDialog
from PyQt5 import QtGui
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget, 
    QTabWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QDialogButtonBox,
    QPushButton,
    QTextEdit,
    QComboBox,
    QRadioButton,
)

class MainTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        layout_vertical_main = QVBoxLayout()
        layout_vertical_graph = QVBoxLayout()


        #Infromación para cargar de la medición
        button = QtWidgets.QPushButton("Añadir Medición")
        button.clicked.connect(self.button_clicked)
        button.setMaximumWidth(150)
        layout_vertical_main.addWidget(button)

        label = QLabel("Nombre de la Medición")
        layout_vertical_main.addWidget(label)

        self.nombre_medicion = QLineEdit()
        layout_vertical_main.addWidget(self.nombre_medicion)

        label = QLabel("Fuente")
        layout_vertical_main.addWidget(label)

        self.fuente = QLineEdit()
        layout_vertical_main.addWidget(self.fuente)

        label = QLabel("Punto de Medición")
        layout_vertical_main.addWidget(label)

        self.punto_medicion = QLineEdit()
        layout_vertical_main.addWidget(self.punto_medicion)

        label = QLabel("Frecuencia de Muestreo")
        layout_vertical_main.addWidget(label)

        self.frecuencia_muestreo = QLineEdit()
        layout_vertical_main.addWidget(self.frecuencia_muestreo)

        label = QLabel("Longitud del Sweep")
        layout_vertical_main.addWidget(label)

        self.long_sweep = QLineEdit()
        layout_vertical_main.addWidget(self.long_sweep)
        
        label = QLabel("Descripción")
        layout_vertical_main.addWidget(label)

        self.descripcion = QTextEdit()
        layout_vertical_main.addWidget(self.descripcion)


        #Botones para elegir configuración
        buttons_layout = QVBoxLayout()
        radio_button_layout = QHBoxLayout()

        self.integration_window_size = 1 * (10 ** -3)
        self.tamaño_ventana = QLabel("Tamaño de la ventana de integración: ")
        buttons_layout.addWidget(self.tamaño_ventana)
        
        self.b1 = QRadioButton("1 ms")
        self.b1.setChecked(True)
        self.b1.toggled.connect(lambda: self.integration_time_selection(self.b1))
        radio_button_layout.addWidget(self.b1)

        self.b2 = QRadioButton("5 ms")
        self.b2.toggled.connect(lambda: self.integration_time_selection(self.b2))
        radio_button_layout.addWidget(self.b2) 

        self.b3 = QRadioButton("10 ms")
        self.b3.toggled.connect(lambda: self.integration_time_selection(self.b3))
        radio_button_layout.addWidget(self.b3)

        buttons_layout.addLayout(radio_button_layout)
        layout_vertical_main.addLayout(buttons_layout)

        self.number_of_windows = 256
        self.cantidad_ventanas_text = QLabel("Ingrese la cantidad de ventanas de integración: ")
        self.cantidad_ventanas_dialog = QLineEdit()
        self.cantidad_ventanas_dialog.setMaximumWidth(75) 

        layout_vertical_main.addWidget(self.cantidad_ventanas_text)
        layout_vertical_main.addWidget(self.cantidad_ventanas_dialog)
        
        self.umbral = 0
        self.umbral_text = QLabel("Ingrese el umbral en dB: ")
        self.umbral_dialog = QLineEdit()
        self.umbral_dialog.setMaximumWidth(75)

        final_button_layout = QHBoxLayout()

        layout_vertical_main.addWidget(self.umbral_text)
        layout_vertical_main.addWidget(self.umbral_dialog)

        graph_button = QPushButton("Graficar")
        graph_button.setMaximumWidth(150)
        graph_button.clicked.connect(self.graficar)

        export_data_button = QPushButton("Exportar Datos")
        export_data_button.setMaximumWidth(150)
        export_data_button.clicked.connect(self.export_data)
        

        final_button_layout.addWidget(graph_button)
        final_button_layout.addWidget(export_data_button)

        #layout_vertical_main.addWidget(graph_button)
        layout_vertical_main.addLayout(final_button_layout)

        #Canvas para gráficos
        self.plot_3D = FigureCanvas(plt.Figure(figsize = (7, 6)))
        layout_vertical_graph.addWidget(self.plot_3D)
        
        self.insert_ax_3D()
        mplcursors.cursor(hover=True)

        self.plot_canalw = FigureCanvas(plt.Figure(figsize = (7, 5)))
        self.insert_ax()
        
        layout_vertical_graph.addWidget(self.plot_canalw)

        layout.addLayout(layout_vertical_main)
        layout.addLayout(layout_vertical_graph)
        
        self.setLayout(layout)

    
    def insert_ax_3D(self):

        self.axes = self.plot_3D.figure.add_subplot(projection = '3d')
        self.cax = self.plot_3D.figure.add_axes([0.85, 0.25, 0.03, 0.5])
        self.axes.set_title("Análisis 3D ")
        self.axes.set_xlabel('X')
        self.axes.set_ylabel('Y')
        self.axes.set_zlabel('Z')
        self.axes.grid(False)
        self.axes.view_init(90, 90)    
        

    def insert_ax(self):

        self.ax = self.plot_canalw.figure.subplots()
        self.ax.set_title("Canal W")
        self.ax.set_xlabel("Tiempo [ms]")
        self.ax.set_ylabel("Amplitud")
        self.ax.grid(True)
        self.line = None


    def button_clicked(self, s):

        print("click", s)
        dlg = CustomDialog(self)
        dlg.exec_()


    def integration_time_selection(self, b):

        if b.text() == "1 ms":
            if b.isChecked() == True:
                self.integration_window_size = 1 * (10 ** -3) 
            else: 
                pass

        if b.text() == "5 ms":
            if b.isChecked() == True:
                self.integration_window_size = 5 * (10 ** -3)
            else: 
                pass
        
        if b.text() == "10 ms":
            if b.isChecked() == True:
                self.integration_window_size = 10 * (10 ** -3)
            else: 
                pass


    def graficar(self):

        datos = Database()
        ambi = datos.get()

        integration_window_size = self.integration_window_size
        try: 
            self.umbral = int(self.umbral_dialog.text())
        except:
            pass

        try: 
            self.number_of_windows = int(self.cantidad_ventanas_dialog.text())
        except: 
            pass
        
        LB = ambi[0]
        LF = ambi[1]
        RB = ambi[2]
        RF = ambi[3]
        Fs = ambi[4]
            
        BLD = LB
        FLU = LF
        BRU = RB
        FRD = RF

        time = np.linspace(0, len(BLD) / Fs, num=len(BLD))


        señal = MainProcessing(BLD, FLU, BRU, FRD, time, Fs, integration_window_size)
        W, X, Y, Z = señal.A_to_B()
        I, az, el = señal.intensity(W, X, Y, Z)  
        I_gr,az_gr,el_gr, time_tr = señal.find_peaks(I, az, el)
        
        I_dB = señal.intensity2dB(I_gr)
        I_dB_th = señal.threshold(I_dB, self.umbral)

        I_dB_th = I_dB_th[0:self.number_of_windows]
        I_norm = señal.normalization(I_dB_th)
        el_gr = el_gr[0:len(I_norm)]
        az_gr = az_gr[0:len(I_norm)]
        time_tr = time_tr[0:len(I_norm)]
        x,y,z = señal.polar2cart(I_norm,az_gr,el_gr)

        self.axes.cla()
        self.cax.clear()

        c = time_tr
        img = self.axes.scatter(x, y, z, c=c, marker=".", linewidths=1, cmap=plt.plasma())

        for i in range(0, len(x)):
            x_val, y_val, z_val = x[i], y[i], z[i]
            if i == 0:
                self.axes.plot([0, x_val], [0, y_val], zs=[0, z_val], color=img.to_rgba(c[i]), linewidth=7)
            elif i > 0:
                self.axes.plot([0, x_val], [0, y_val], zs=[0, z_val], color=img.to_rgba(c[i]), linewidth=2)

        self.save_image()
     
        cbar = self.plot_3D.figure.colorbar(img, pad = 0.25, use_gridspec = True, cax = self.cax)
        cbar.set_label("Tiempo [ms]")

        self.plot_3D.draw() 

        self.line = self.ax.plot(time, W, color='b')       
        self.plot_canalw.draw()

        self.data = señal.table(time_tr,I_dB_th,az_gr,el_gr)


    def save_image(self):
        self.axes.axis("off")
        self.axes.set_title("")
        self.cax.axis("off")
        self.plot_3D.figure.savefig('./RIR_3D.png', transparent = True)
        self.axes.axis("on")
        self.axes.set_title("Análisis 3D")
        self.cax.axis("on")


    def export_data(self):
        
        nombre = self.nombre_medicion.text()
        self.data['Nombre medición'] = nombre

        fuente = self.fuente.text()
        self.data['Fuente'] = fuente

        punto_medicion = self.punto_medicion.text()
        self.data['Punto de Medición'] = punto_medicion

        frecuencia_muestreo = self.frecuencia_muestreo.text()
        self.data['Frecuencia de Muestreo'] = frecuencia_muestreo

        longitud_sweep = self.long_sweep.text()
        self.data['Longitud del Sweep'] = longitud_sweep

        descripcion = self.descripcion.toPlainText()
        self.data['Descripción'] = descripcion
          
        self.data.to_excel('./Datos_rir.xlsx')