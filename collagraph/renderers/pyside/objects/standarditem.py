from PySide6.QtGui import QStandardItem

from ... import PySideRenderer
from .qobject import set_attribute as qobject_set_attribute


@PySideRenderer.register_insert(QStandardItem)
def insert(self, el, anchor=None):
    if hasattr(el, "model_index"):
        row, column = getattr(el, "model_index")
        self.setChild(row, column, el)
        return

    if anchor is not None:
        index = None
        for row in range(self.rowCount()):
            if anchor is self.child(row):
                index = row
                break
        if index is None:
            return
        self.insertRow(index, el)
    else:
        self.appendRow(el)


@PySideRenderer.register_remove(QStandardItem)
def remove(self, el):
    if hasattr(el, "model_index"):
        # Only support removal of rows for now
        row, column = getattr(el, "model_index")
        if model := el.model():
            index = model.indexFromItem(el)
            row = index.row()

        self.takeRow(row)
        return

    self.takeRow(el.row())


@PySideRenderer.register_set_attr(QStandardItem)
def set_attribute(self, attr, value):
    if attr == "model_index":
        if model := self.model():
            index = model.indexFromItem(self)
            row, column = value
            if index.row() != row or index.column() != column:
                if parent := self.parent():
                    # `it` is `self`
                    it = parent.takeChild(index.row(), index.column())
                    parent.setChild(row, column, self)
                else:
                    # `it` is `self`
                    it = model.takeItem(index.row(), index.column())
                    model.setItem(row, column, it)

    qobject_set_attribute(self, attr, value)
