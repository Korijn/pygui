"""
Example of how to render to PySide6 UI and utilize
the layout of widgets.
"""

from observ import reactive
from PySide6 import QtWidgets

import collagraph as cg
from collagraph import h
from examples.pyside.flow_layout import FlowLayout

cg.PySideRenderer.register_layout("flow", FlowLayout)


def LayoutExample(props):
    index = props.get("index", 0)

    def accepted():
        print("accepted")  # noqa: T201

    def rejected():
        print("rejected")  # noqa: T201

    def select_all():
        print("select all")  # noqa: T201

    def clicked(btn):
        print("clicked:", btn)  # noqa: T201

    def set_index(number):
        props["index"] = number - 1

    # Data to fill the box layout
    box = []
    for i in range(1, 5):
        box.append(
            (
                "Button",
                {
                    "text": f"Button {i}",
                    "on_clicked": lambda _=None, x=i: set_index(x),
                },
            )
        )

    # Data to fill the grid layout
    grid = []
    for i in range(1, 5):
        grid.append(("Label", {"text": f"Line {i}", "grid_index": (i, 0)}))
        grid.append(("LineEdit", {"grid_index": (i, 1)}))
    grid.append(
        (
            "TextEdit",
            {
                "text": "This widget takes up about two thirds of the grid layout",
                "grid_index": (1, 2, 4, 1),
            },
        )
    )

    # Data to fill the form layout
    form = []
    for i, widget in enumerate(["LineEdit", "ComboBox", "SpinBox"]):
        text = f"Line {i+1}:"
        if i == 1:
            text = "Line 2, long text:"
        form.append((widget, {"form_label": text, "form_index": i}))

    stacked = []
    for i in range(1, 5):
        stacked.append(("Label", {"text": f"Stack {i}"}))

    flow = []
    for i in range(1, 10):
        flow.append(("label", {"text": f"Flow {i}"}))

    return h(
        "Window",
        {},
        h(
            "MenuBar",
            {},
            h(
                "QMenu",
                {"title": "File"},
                h("QAction", {"text": "Open"}),
                h("QAction", {"separator": True}),
                h("QMenu", {"title": "Sub"}, h("QAction", {"text": "sub"})),
            ),
        ),
        h(
            "Widget",
            {},
            h(
                "GroupBox",
                {
                    "title": "Horizontal layout",
                    "layout": {
                        "type": "Box",
                        "direction": "LeftToRight",
                    },
                },
                *[h(item[0], item[1]) for item in box],
            ),
            h(
                "GroupBox",
                {
                    "title": "Stacked layout",
                    "layout": {
                        "type": "Stacked",
                        "current_index": index,
                    },
                },
                *[h(item[0], item[1]) for item in stacked],
            ),
            h(
                "GroupBox",
                {
                    "title": "Flow layout (custom)",
                    "layout": {
                        "type": "flow",
                    },
                },
                *[h(item[0], item[1]) for item in flow],
            ),
            h(
                "GroupBox",
                {
                    "title": "Grid layout",
                    "layout": {
                        "type": "Grid",
                        # Other possible props:
                        # - row_stretch
                        # - column_minimum_width
                        # - row_minimum_height
                        # - vertical_spacing
                        # - horizontal_spacing
                        "column_stretch": [(1, 10), (2, 20)],
                    },
                },
                *[h(item[0], item[1]) for item in grid],
            ),
            h(
                "GroupBox",
                {
                    "title": "Form layout",
                    "layout": {
                        "type": "Form",
                    },
                },
                *[h(item[0], item[1]) for item in form],
            ),
            h(
                "TextEdit",
                {
                    "text": "This widget takes up all the remaining "
                    "space in the top-level layout."
                },
            ),
            h(
                "DialogButtonBox",
                {
                    "on_accepted": accepted,
                    "on_rejected": rejected,
                    "on_clicked": clicked,
                    # Provide a list of standard buttons to add to the dialog box.
                    # See `QDialogButtonBox.ButtonRole` enum for more info.
                    "buttons": ("Ok", "Cancel"),
                },
                # Add custom buttons by adding real buttons and specifying a
                # `role` attribute that will determine where the button will
                # end up in the botton box.
                # See `QDialogButtonBox.ButtonRole` enum for more info.
                h(
                    "Button",
                    {
                        "text": "Select all",
                        "role": "ResetRole",
                        "on_clicked": select_all,
                    },
                ),
            ),
        ),
    )


if __name__ == "__main__":
    app = QtWidgets.QApplication()

    gui = cg.Collagraph(renderer=cg.PySideRenderer())

    state = reactive({})
    # Define Qt structure and map state to the structure
    element = h(LayoutExample, state)

    # Pass in the app as a container. Can actually be any truthy object
    gui.render(element, app)
    app.exec()
