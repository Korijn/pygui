from observ import reactive
from PySide6 import QtWidgets

import collagraph as cg

app = QtWidgets.QApplication()


def changed(idx):
    state["currentIndex"] = idx


state = reactive(
    {
        "items": [
            "tree",
            "dog",
            "horse",
        ],
        "current_index": 2,
        "on_current_index_changed": changed,
    }
)


gui = cg.Collagraph(renderer=cg.PySideRenderer())
gui.render(
    cg.h(
        "widget",
        {},
        cg.h(
            "qcombobox",
            state,
        ),
    ),
    app,
)

app.exec()
