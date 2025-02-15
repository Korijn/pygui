import logging

from PySide6.QtCore import QItemSelectionModel
from PySide6.QtGui import QAction, QStandardItemModel

from ... import PySideRenderer
from .. import attr_name_to_method_name, call_method

logger = logging.getLogger(__name__)


@PySideRenderer.register_set_attr(QAction, QStandardItemModel, QItemSelectionModel)
def set_attribute(self, attr, value):
    method_name = attr_name_to_method_name(attr, setter=True)
    method = getattr(self, method_name, None)
    if not method:
        logger.debug(f"Setting custom attr: {attr}")
        setattr(self, attr, value)
        return

    call_method(method, value)
