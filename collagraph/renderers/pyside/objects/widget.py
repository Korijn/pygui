import logging

from PySide6.QtWidgets import QWidget

from ...pyside_renderer import PySideRenderer
from .layouts import remove_layout
from .qobject import set_attribute as qobject_set_attribute

logger = logging.getLogger(__name__)


@PySideRenderer.register_insert(QWidget)
def insert(self, el, anchor=None):
    el.setParent(self)

    # Adding a widget (el) to a widget (self) involves getting the layout
    # of the parent (self) and then inserting the widget into the layout.
    # The layout might not exist yet, so let's create a default QBoxLayout.
    layout = self.layout()
    if not layout:
        layout = PySideRenderer.create_object("box")
        self.setLayout(layout)

    layout.insert(el, anchor=anchor)


@PySideRenderer.register_remove(QWidget)
def remove(self, el):
    layout = self.layout()
    if hasattr(layout, "remove"):
        # Call the registered custom method of the wrapped layout
        layout.remove(el)
    else:
        # Some layouts in the hierarchy are not wrapped
        # because PySide creates them internally, hence
        # the need to have a fallback
        remove_layout(layout, el)


@PySideRenderer.register_set_attr(QWidget)
def set_attribute(self, attr, value):
    if attr == "size":
        self.resize(*value)
        return

    qobject_set_attribute(self, attr, value)
