from PySide6 import QtWidgets

import collagraph as cg

if __name__ == "__main__":
    from tests.data.pyside.app import Window

    app = QtWidgets.QApplication()
    gui = cg.Collagraph(renderer=cg.PySideRenderer())
    gui.render(Window, app)
    app.exec()
