import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtGui, QtWidgets

import collagraph as cg


def test_recursive_change(qtbot):
    from tests.data.pyside.test_pyside_update import TreeView

    renderer = cg.PySideRenderer(autoshow=False)
    container = renderer.create_element("widget")

    gui = cg.Collagraph(renderer=renderer)
    gui.render(TreeView, container)

    button = None
    item_model = None
    selection_model = None

    def find_button():
        nonlocal button
        nonlocal item_model
        nonlocal selection_model
        button = container.findChild(QtWidgets.QPushButton, "button")
        assert button
        item_model = container.findChild(QtGui.QStandardItemModel, "item-model")
        assert item_model
        selection_model = container.findChild(
            QtCore.QItemSelectionModel, "selection-model"
        )
        assert selection_model

    qtbot.waitUntil(find_button, timeout=500)

    assert not button.isEnabled()

    selection_model.select(
        item_model.index(2, 0), QtCore.QItemSelectionModel.ClearAndSelect
    )

    qtbot.waitUntil(lambda: button.isEnabled(), timeout=500)

    qtbot.mouseClick(button, QtCore.Qt.LeftButton)

    qtbot.waitUntil(lambda: not button.isEnabled(), timeout=500)
