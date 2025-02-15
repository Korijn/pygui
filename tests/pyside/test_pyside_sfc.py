import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

import collagraph as cg


def test_pyside_sfc_event_handlers(qtbot, parse_source):
    """Test that methods on Component class can work as event handlers in PySide."""
    Buttons, _ = parse_source(
        """
        <widget>
          <button v-on:clicked="increase" text="Add" object_name="add" />
          <button @clicked="decrease" text="Sub" object_name="dec" />
          <label :text="str(count)" />
        </widget>

        <script>
        import collagraph as cg

        class Buttons(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["count"] = 0

            def increase(self):
                self.state["count"] += 1

            def decrease(self):
                self.state["count"] -= 1
        </script>
        """
    )

    renderer = cg.PySideRenderer(autoshow=False)
    gui = cg.Collagraph(renderer=renderer)
    container = renderer.create_element("widget")
    gui.render(Buttons, container)

    label = None
    add_button = None
    dec_button = None

    def widgets_are_found():
        nonlocal label
        nonlocal add_button
        nonlocal dec_button
        label = container.findChild(QtWidgets.QLabel)
        add_button = container.findChild(QtWidgets.QPushButton, name="add")
        dec_button = container.findChild(QtWidgets.QPushButton, name="dec")
        assert label and add_button and dec_button

    qtbot.waitUntil(widgets_are_found, timeout=500)

    assert label.text() == "0"

    qtbot.mouseClick(add_button, QtCore.Qt.LeftButton)
    qtbot.waitUntil(lambda: label.text() == "1", timeout=500)
    qtbot.mouseClick(dec_button, QtCore.Qt.LeftButton)
    qtbot.waitUntil(lambda: label.text() == "0", timeout=500)
