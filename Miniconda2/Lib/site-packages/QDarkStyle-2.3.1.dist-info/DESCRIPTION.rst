
This package provides a dark style sheet for PySide/PyQt4/PyQt5 applications.

All you have to do is the following::

    import qdarkstyle
    app = QtGui.QApplication().instance()
    # PySide
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    # PyQt4
    app.setStyleSheet(qdarkstyle.load_stylesheet(pyside=False))
    # PyQt5
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())



