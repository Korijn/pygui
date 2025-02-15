from PySide6 import QtWidgets

from ... import PySideRenderer
from . import widget


@PySideRenderer.register_set_attr(QtWidgets.QComboBox)
def set_attribute(self, attr, value):
    if attr == "items":
        self.addItems(value)
    else:
        widget.set_attribute(self, attr, value)
