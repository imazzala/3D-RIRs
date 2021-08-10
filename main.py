import sys
from PyQt5 import QtCore, QtWidgets

from main_tab import MainTab
from vistas import Vistas
from acustical_parameters_view import AcusticalParametersView

from PyQt5.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout, 
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit, 
    QPushButton,
    QFormLayout,    
    QTextEdit
    )

class MainWindow(QMainWindow):
    
    def __init__(self, *args, **kwargs):

        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("RIR 3D")
        self.setGeometry(200, 100, 1080, 920)

        tabWidget = QTabWidget()
        tabWidget.addTab(MainTab(), "Main")
        tabWidget.addTab(Vistas(), "Views")
        tabWidget.addTab(AcusticalParametersView(), "Acoustical Parameters")

        self.setCentralWidget(tabWidget)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec_()