"""
Example of how to render lists, tables and trees.
"""

from observ import reactive
from PySide6 import QtCore, QtWidgets

import collagraph as cg
from collagraph import h

STATE_MAP = {
    False: QtCore.Qt.Unchecked,
    True: QtCore.Qt.Checked,
}


def Example(props):
    def bump():
        props["items"].append([["NEW", "ITEM"], False])

    def decr():
        if len(props["items"]):
            props["items"].pop(0)

    def item_changed(item):
        props["items"][item.row()][0][item.column()] = item.text()
        props["items"][item.row()][1] = item.checkState() == QtCore.Qt.Checked

    def selection_changed(selected, deselected):
        sel = [(idx.row(), idx.column()) for idx in selected.indexes()]
        desel = [(idx.row(), idx.column()) for idx in deselected.indexes()]
        print(desel, "=>", sel)  # noqa: T201

    children = []
    for row, (item, check_state) in enumerate(props["items"]):
        for column, text in enumerate(item):
            child_props = {
                "text": text,
                "model_index": (row, column),
                "checkable": column == 0,
            }
            if column == 0:
                child_props["check_state"] = STATE_MAP[check_state]
            children.append(h("QStandardItem", child_props))

    item_model = h(
        "QStandardItemModel",
        {
            "on_item_changed": item_changed,
            "column_count": 2,
        },
        *children
    )
    selection_model = h(
        "QItemSelectionModel",
        {"on_selection_changed": selection_changed},
    )

    return h(
        "Window",
        {},
        h(
            "Widget",
            {},
            h(
                "QSplitter",
                {},
                h(
                    "QListView",
                    {},
                    item_model,
                    selection_model,
                    # NOTE: the order of `item_model` and `selection_model` matters:
                    # the item model needs to come before the selection model, because
                    # the selection model needs an item model in order to function and
                    # `setSelectionModel` call will fail with the following message:
                    #
                    #   > QAbstractItemView::setSelectionModel() failed: Trying to set
                    #   > a selection model, which works on a different model than the
                    #   > view.
                ),
                h(
                    "QTableView",
                    {},
                    item_model,
                    selection_model,
                ),
                h(
                    "QTreeView",
                    {},
                    item_model,
                    selection_model,
                ),
            ),
            h(
                "Widget",
                {
                    "layout": {
                        "type": "Box",
                        "direction": "LeftToRight",
                    },
                    "maximum-height": 50,
                },
                h("Button", {"text": "Add", "on_clicked": bump, "object_name": "add"}),
                h(
                    "Button",
                    {"text": "Remove", "on_clicked": decr, "object_name": "remove"},
                ),
            ),
        ),
    )


if __name__ == "__main__":
    app = QtWidgets.QApplication()

    gui = cg.Collagraph(renderer=cg.PySideRenderer())

    state = reactive(
        {
            "items": [
                [["Item", "Value"], False],
                [["Foo", "Bar"], False],
            ],
        }
    )

    # Define Qt structure and map state to the structure
    element = h(Example, state)

    # Pass in the app as a container. Can actually be any truthy object
    gui.render(element, app)
    app.exec()
