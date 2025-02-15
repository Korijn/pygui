from PySide6.QtWidgets import (
    QBoxLayout,
    QFormLayout,
    QGridLayout,
    QLayout,
    QStackedLayout,
    QWidget,
)

from ...pyside_renderer import LAYOUT_MAPPING, PySideRenderer
from .. import attr_name_to_method_name, call_method

DIRECTIONS = {
    "TopToBottom": QBoxLayout.Direction.TopToBottom,
    "LeftToRight": QBoxLayout.Direction.LeftToRight,
    "RightToLeft": QBoxLayout.Direction.RightToLeft,
    "BottomToTop": QBoxLayout.Direction.BottomToTop,
}


PySideRenderer.register_layout("box", QBoxLayout)
PySideRenderer.register_layout("form", QFormLayout)
PySideRenderer.register_layout("grid", QGridLayout)
PySideRenderer.register_layout("stacked", QStackedLayout)


@PySideRenderer.register_insert(QLayout)
def layout_insert(self, el, anchor=None):
    self.addWidget(el)


@PySideRenderer.register_insert(QBoxLayout, QStackedLayout)
def box_layout_insert(self, el, anchor=None):
    index = -1
    if anchor is not None:
        index = self.indexOf(anchor)

    self.insertWidget(index, el)


@PySideRenderer.register_insert(QFormLayout)
def form_insert(self, el, anchor=None):
    if hasattr(el, "form_index"):
        self.insertRow(el.form_index, el.form_label, el)
    else:
        self.addRow(el.form_label, el)


@PySideRenderer.register_insert(QGridLayout)
def grid_insert(self, el, anchor=None):
    self.addWidget(el, *el.grid_index)


@PySideRenderer.register_remove(QLayout)
def remove_layout(self, el):
    self.removeWidget(el)
    el.setParent(None)


@PySideRenderer.register_remove(QFormLayout)
def remove_form(self, el):
    # Layout also deletes 'el' so no need to unset parent
    self.removeRow(el)


@PySideRenderer.register_set_attr(QLayout)
def set_layout_attribute(self, attr, value):
    if attr == "type":
        return
    method_name = attr_name_to_method_name(attr, setter=True)
    if method := getattr(self.layout(), method_name, None):
        if attr in {"direction"}:
            arg = DIRECTIONS[value]
            call_method(method, arg)
        elif attr in {"column_stretch", "row_stretch"}:
            for args in value:
                call_method(method, args)
        else:
            call_method(method, value)


@PySideRenderer.register_custom_attribute("layout")
def set_layout_attr(self, attr, value):
    if layout_type := LAYOUT_MAPPING.get(value["type"].lower()):
        layout = self.layout()
        if isinstance(layout, layout_type):
            pass
        else:
            if layout:
                QWidget().setLayout(layout)
            layout = PySideRenderer.create_object(value["type"].lower())
            self.setLayout(layout)

        for key, val in value.items():
            layout.set_attribute(key, val)
    else:
        raise RuntimeError(f"No layout registered for type: {value['type']}")


@PySideRenderer.register_custom_attribute("grid_index")
def set_grid_index(self, attr, value):
    self.grid_index = value
    if parent := self.parent():
        layout = parent.layout()
        layout.addWidget(self, *value)


@PySideRenderer.register_custom_attribute("form_label", "form_index")
def set_form_index(self, attr, value):
    setattr(self, attr, value)
    if parent := self.parent():
        layout = parent.layout()
        if hasattr(self, "form_label") and hasattr(self, "form_index"):
            layout.insertRow(self.form_index, self.form_label, self)
        elif hasattr(self, "form_label"):
            layout.addRow(self.form_label, self)
