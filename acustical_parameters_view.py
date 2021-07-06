import sys
from PyQt5 import QtCore
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import mplcursors
import parameters
from singleton import Database
import pandas as pd

matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtCore import Qt
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QLine, lowercasebase, qrand
from PyQt5.QtGui import QIcon, QRasterWindow, QTabletEvent, QTextLayout
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
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
    QTableWidget,
    QGroupBox
)
from matplotlib.backends.backend_agg import FigureCanvasAgg
from numpy import set_string_function


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role = QtCore.Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])

    def rowCount(self, index):
        return len(self._data[['31.5']])

    def columnCount(self, index):
        return len(self._data.iloc[index.column()])

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._data.columns[section]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return self._data.index[section]
        return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)
        


class AcusticalParametersView(QWidget):
    def __init__(self):
        super().__init__()
        
        vLayout = QVBoxLayout()
        layout = QHBoxLayout()

        vBox = QVBoxLayout()
        vBox.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        qlabel = QLabel("Parámetros de Cálculo: ")
        vBox.addWidget(qlabel)

        self.trunc = 0
        lundeby_box = QGroupBox('Truncar por Lundeby')
        lundeby_box.setMaximumWidth(230)
        lundeby_box.setLayout(QHBoxLayout()) 

        self.yes_button = QRadioButton("Sí")
        self.yes_button.setChecked(True)
        self.yes_button.toggled.connect(lambda: self.lundeby_selection(self.yes_button))
        
        self.no_button = QRadioButton("No")
        self.no_button.toggled.connect(lambda: self.lundeby_selection(self.no_button))

        lundeby_box.layout().addWidget(self.yes_button) 
        lundeby_box.layout().addWidget(self.no_button) 
        vBox.addWidget(lundeby_box)

        self.divi = 0
        suavizado_box = QGroupBox('Suavizado')
        suavizado_box.setMaximumWidth(230)
        suavizado_box.setLayout(QHBoxLayout()) 
        
        self.schroeder_button = QRadioButton('Schroeder')
        self.schroeder_button.setChecked(True)
        self.schroeder_button.toggled.connect(lambda: self.suavizado_selection(self.schroeder_button))
        
        self.mmf_button = QRadioButton('MMF')
        self.mmf_button.toggled.connect(lambda: self.suavizado_selection(self.mmf_button))
        
        suavizado_box.layout().addWidget(self.schroeder_button) 
        suavizado_box.layout().addWidget(self.mmf_button) 
        vBox.addWidget(suavizado_box)

        self.smooth = 0
        filtrado_box = QGroupBox('Suavizado')
        filtrado_box.setMaximumWidth(230)
        filtrado_box.setLayout(QHBoxLayout()) 
        
        self.octave_button = QRadioButton("Octava")
        self.octave_button.setChecked(True)
        self.octave_button.toggled.connect(lambda: self.filter_selection(self.octave_button))
        
        self.ter_octave_button = QRadioButton("Tercio de Octava")
        self.ter_octave_button.toggled.connect(lambda: self.filter_selection(self.ter_octave_button))
        
        filtrado_box.layout().addWidget(self.octave_button) 
        filtrado_box.layout().addWidget(self.ter_octave_button) 
        vBox.addWidget(filtrado_box)

        self.vent = 20
        window_size_label = QLabel("Tamaño de la ventana de integración en ms")
        vBox.addWidget(window_size_label)

        self.window_size_line = QLineEdit()
        self.window_size_line.setMaximumWidth(75)

        vBox.addWidget(self.window_size_line)
        
        Hlay = QHBoxLayout()
        
        calc_button = QPushButton("Calcular")
        calc_button.setMaximumWidth(150)
        calc_button.clicked.connect(self.calculation)

        export_button = QPushButton("Exportar")
        export_button.setMaximumWidth(150)
        export_button.clicked.connect(self.export_data)

        Hlay.addWidget(calc_button)
        Hlay.addWidget(export_button)

        vBox.addLayout(Hlay)


        #Grafico y Tabla

        parameters = {'axes.labelsize': 5, 'axes.titlesize': 5, 
                    'xtick.labelsize': 5, 'ytick.labelsize': 5}
        plt.rcParams.update(parameters)

        self.plot_rir = FigureCanvas(plt.figure(figsize = (4, 1.5)))
        self.insert_ax()

        layout.addLayout(vBox)
        layout.addWidget(self.plot_rir)

        self.filter_selected = 0

        self.table = QtWidgets.QTableView()

        vLayout.addLayout(layout)
        vLayout.addWidget(self.table)

        self.setLayout(vLayout)

        
    def insert_ax(self):

        self.ax = self.plot_rir.figure.subplots()
        self.ax.set_title("Respuesta al Impulso")
        self.ax.set_xlabel("Tiempo [ms]")
        self.ax.set_ylabel("Amplitud")
        self.ax.grid(True)
        self.line = None


    def filter_selection(self, b):

        #b = self.sender()        
        if b.text() == "Octava":
            if b.isChecked() == True: 
                self.divi = 0
                print(self.divi)
            else:
                pass
        
        if b.text() == "Tercio de Octava":
            if b.isChecked() == True: 
                self.divi = 1
                print(self.divi)
            else: 
                pass
    

    def lundeby_selection(self, b):

        b = self.sender()
        if b.text() == "Sí":

            if b.isChecked() == True: 
                self.trunc = 0
            else:
                pass

        if b.text() == "No":
            
            if b.isChecked() == True:
                self.trunc = 1
            else: 
                pass


    def suavizado_selection(self, b):

        b = self.sender()
        if b.text() == "Schroeder":

            if b.isChecked() == True: 
                self.smooth = 0
            else:
                pass

        if b.text() == "MMF":
            
            if b.isChecked() == True:
                self.smooth = 1                
            else: 
                pass


    def calculation(self):

        datos = Database()
        ambi = datos.get()

        LB = ambi[0]
        LF = ambi[1]
        RB = ambi[2]
        RF = ambi[3]
        fs = ambi[4]
        
        BLD = LB
        FLU = LF
        BRU = RB
        FRD = RF

        W = FLU + FRD + BLD + BRU
        Y = FLU - FRD + BLD - BRU

        W = np.transpose(W)
        Y = np.transpose(Y)
        
        try:
            self.vent = int(self.window_size_line.text())
        except:
            pass


        Tt, EDTt, C50,C80,EDT,T20,T30,IACCe, ir, sm = parameters.ac_parameters(self.divi,self.trunc,self.smooth,self.vent, W, Y, fs)
        self.data = parameters.table(Tt, EDTt, C50,C80,EDT,T20,T30,IACCe,self.divi)
    
        self.model = TableModel(self.data)
        self.table.setModel(self.model)
        
        self.ax.cla()
        
        t = np.arange(0, len(ir[-1]) / fs, 1 / fs)
        t = t[:len(ir[-1])]

        self.ax.plot(t, ir[-1],label='Impulse Response')

        if self.smooth == 0:
            self.ax.plot(t, sm[-1], label='Schroeder Decay')
        elif self.smooth == 1:
            self.ax.plot(t, sm[-1], label='Mov. Median Filter Decay ')
        self.ax.set_ylim([-100, 3])

        self.plot_rir.draw()


    def export_data(self):
        self.data.to_excel('./Acustical_Parameters.xlsx')
        self.plot_rir.figure.savefig('./RIR_y_suavizado.png')




