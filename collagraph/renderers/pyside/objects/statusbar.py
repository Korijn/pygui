from PySide6.QtWidgets import QStatusBar

from ... import PySideRenderer
from . import widget


@PySideRenderer.register_insert(QStatusBar)
def insert(self, el, anchor=None):
    # TODO: support for anchor
    # Support for anchor would be tough: there is no API to get
    # the index of an element, so some custom bookkeeping needs
    # to take place. But also, when a message is displayed, the
    # non-permanent widgets seem to get cleared?
    # And when I tried to remove a permanent widget with a v-if
    # statement, a non-permanent widget was shown in the
    # permanent section... so I guess we need a better understanding
    # of this widget before adding anchor support.
    if getattr(el, "permanent", False):
        self.addPermanentWidget(el)
    else:
        self.addWidget(el)
    el.setParent(self)


@PySideRenderer.register_remove(QStatusBar)
def remove(self, el):
    self.removeWidget(el)
    el.setParent(None)


@PySideRenderer.register_set_attr(QStatusBar)
def set_attribute(self, attr, value):
    if attr == "text":
        if isinstance(value, tuple):
            self.showMessage(*value)
        else:
            self.showMessage(value)
    else:
        widget.set_attribute(self, attr, value)
