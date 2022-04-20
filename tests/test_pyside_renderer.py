import pytest


try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    pytest.skip(
        "skip test for PySide6 renderer when not available", allow_module_level=True
    )


from collagraph import Collagraph, create_element as h, EventLoopType
from collagraph.renderers import PySideRenderer


# Make sure a Qt application already exists
QtCore.QCoreApplication.instance() or QtWidgets.QApplication()


def test_simple_widget():
    renderer = PySideRenderer()
    gui = Collagraph(renderer=renderer, event_loop_type=EventLoopType.SYNC)

    element = h("Widget", {"layout": {"type": "Box", "direction": "RightToLeft"}})
    container = renderer.create_element("Widget")
    gui.render(element, container)

    # Test the default direction of box layout
    assert container.layout().direction() == QtWidgets.QBoxLayout.Direction.TopToBottom
    el = container.findChild(QtWidgets.QWidget)
    # Test the custom direction for the widget
    assert el.layout().direction() == QtWidgets.QBoxLayout.Direction.RightToLeft


def test_label():
    renderer = PySideRenderer()
    gui = Collagraph(renderer=renderer, event_loop_type=EventLoopType.SYNC)

    element = h("Widget", {"layout": {"type": "Box"}}, h("Label", {"text": "Foo"}))
    container = renderer.create_element("Window")
    gui.render(element, container)

    label = container.findChild(QtWidgets.QLabel)
    assert label.text() == "Foo"