from PySide6.QtWidgets import QTreeWidgetItem

from ... import PySideRenderer
from .qobject import set_attribute as qobject_set_attribute


@PySideRenderer.register_insert(QTreeWidgetItem)
def insert(self, el: QTreeWidgetItem, anchor=None):
    if not isinstance(el, QTreeWidgetItem):
        raise NotImplementedError(f"No insert defined for: {type(el).__name__}")

    if anchor is not None:
        index = self.indexOfChild(anchor)
        if el.parent():
            self.removeChild(el)
        self.insertChild(index, el)
    else:
        self.addChild(el)

    # After mounting, process some attributes that can only
    # be adjusted when the item is mounted in the tree structure
    if hasattr(el, "_expanded"):
        el.setExpanded(el._expanded)
        delattr(el, "_expanded")

    if hasattr(el, "_selected"):
        el.setSelected(el._selected)
        delattr(el, "_selected")


@PySideRenderer.register_remove(QTreeWidgetItem)
def remove(self, el: QTreeWidgetItem):
    self.removeChild(el)


@PySideRenderer.register_set_attr(QTreeWidgetItem)
def set_attribute(self, attr, value):
    if attr == "content":
        for col, data in value.items():
            self.setText(col, data)
        return
    elif attr == "expanded":
        if not self.parent():
            self._expanded = value
        else:
            self.setExpanded(value)
        return
    elif attr == "selected":
        if not self.parent():
            self._selected = value
        else:
            self.setSelected(value)
        return

    qobject_set_attribute(self, attr, value)
