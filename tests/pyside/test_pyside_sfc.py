import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

import collagraph as cg
from collagraph.cgx import cgx


def test_pyside_sfc_event_handlers(qapp, qtbot):
    """Test that class methods can work as event handlers in PySide."""
    Buttons, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <!-- Normal on -->
            <button v-on:clicked="increase" text="Add" object_name="add" />
            <!-- Shortcut on -->
            <button @clicked="decrease" text="Sub" object_name="dec" />
            <label :text="counter_text()" />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Buttons(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["count"] = 0

            def increase(self):
                self.state["count"] += 1

            def decrease(self):
                self.state["count"] -= 1

            def counter_text(self):
                return str(self.state["count"])
        </script>
        """
    )

    renderer = cg.PySideRenderer(autoshow=False)
    gui = cg.Collagraph(renderer=renderer, event_loop_type=cg.EventLoopType.QT)
    container = renderer.create_element("widget")
    gui.render(cg.h(Buttons, {}), container)

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
