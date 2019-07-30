import sys
import os
SVFHOME = os.environ['SVFHOME']
sys.path.insert(0, SVFHOME + 'SegnetCUDA/pycaffe')
import SVFMap
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *

if __name__ == "__main__":
    app = SVFMap.QApplication(sys.argv)
    app.setWindowIcon(QIcon(SVFHOME + "Icons/App.png"))
    #app.setStyle("plastique")
    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    main = SVFMap.Browser()
    main.setWindowTitle('GSV2SVF')
    main.show()
    main.initialize()
    sys.exit(app.exec_())