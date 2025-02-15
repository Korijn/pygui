import textwrap

import pytest
from observ import reactive

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

import collagraph as cg
from collagraph.sfc.compiler import load_from_string


def test_widget_size():
    renderer = cg.PySideRenderer(autoshow=False)
    widget = renderer.create_element("widget")
    renderer.set_attribute(widget, "size", (600, 400))

    assert widget.size().width() == 600
    assert widget.size().height() == 400


def test_widget_close():
    closed = False

    def close(event):
        nonlocal closed
        closed = True

    renderer = cg.PySideRenderer(autoshow=False)
    widget = renderer.create_element("widget")
    renderer.add_event_listener(widget, "close", close)

    widget.close()

    assert closed is True


def test_widget_as_window(qapp, qtbot):
    Widget, _ = load_from_string(
        textwrap.dedent(
            """
        <widget />

        <script>
        import collagraph as cg
        class Widget(cg.Component):
            pass
        </script>
        """
        )
    )
    renderer = cg.PySideRenderer(autoshow=False)
    gui = cg.Collagraph(renderer=renderer)
    gui.render(Widget, qapp)

    def check_widget_as_window():
        windows = qapp.topLevelWidgets()
        assert len(windows) == 1

    qtbot.waitUntil(check_widget_as_window, timeout=500)


def test_widget_switch_layouts(qapp, qtbot):
    SwitchLayouts, _ = load_from_string(
        textwrap.dedent(
            """
        <widget :layout="layout" />

        <script>
        import collagraph as cg
        class SwitchLayouts(cg.Component):
            pass
        </script>
        """
        )
    )

    state = reactive({"layout": {"type": "box"}})

    renderer = cg.PySideRenderer(autoshow=False)
    gui = cg.Collagraph(renderer=renderer)
    gui.render(SwitchLayouts, qapp, state=state)

    widget = None

    def check_widget():
        nonlocal widget
        windows = qapp.topLevelWidgets()
        assert len(windows) == 1
        widget = windows[0]

    qtbot.waitUntil(check_widget, timeout=1500)
    qtbot.waitUntil(
        lambda: isinstance(widget.layout(), QtWidgets.QBoxLayout), timeout=500
    )

    state["layout"]["type"] = "grid"

    qtbot.waitUntil(
        lambda: isinstance(widget.layout(), QtWidgets.QGridLayout), timeout=500
    )

    state["layout"]["type"] = "form"

    qtbot.waitUntil(
        lambda: isinstance(widget.layout(), QtWidgets.QFormLayout), timeout=500
    )

    state["layout"]["type"] = "box"

    qtbot.waitUntil(
        lambda: isinstance(widget.layout(), QtWidgets.QBoxLayout), timeout=500
    )
