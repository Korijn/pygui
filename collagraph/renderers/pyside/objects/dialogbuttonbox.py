from PySide6.QtWidgets import QDialogButtonBox

from ... import PySideRenderer
from .widget import set_attribute as widget_set_attribute


@PySideRenderer.register_insert(QDialogButtonBox)
def insert(self, el, anchor=None):
    if hasattr(el, "role"):
        # Allow the role to be either an actual ButtonRole or a string
        role = (
            el.role
            if isinstance(el.role, QDialogButtonBox.ButtonRole)
            else getattr(QDialogButtonBox, el.role)
        )
        self.addButton(el, role)
        return
    raise NotImplementedError


@PySideRenderer.register_set_attr(QDialogButtonBox)
def set_attribute(self, attr, value):
    if attr == "buttons":
        for flag in value:
            flag = (
                flag
                if isinstance(flag, QDialogButtonBox.StandardButton)
                else getattr(QDialogButtonBox, flag)
            )
            self.addButton(flag)
    else:
        widget_set_attribute(self, attr, value)
