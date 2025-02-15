[![PyPI version](https://badge.fury.io/py/collagraph.svg)](https://badge.fury.io/py/collagraph)
[![CI status](https://github.com/fork-tongue/collagraph/workflows/CI/badge.svg)](https://github.com/fork-tongue/collagraph/actions)

# Collagraph 📓

Reactive user interfaces.

> The word [Collagraphy](https://en.wikipedia.org/wiki/Collagraphy) is derived from the Greek word _koll_ or _kolla_, meaning glue, and graph, meaning the activity of drawing.

Inspired by Vue and React.


## Features

Write your Python interfaces in a declarative manner with plain render functions, component classes or even single-file components using Vue-like syntax, but with Python!

* Reactivity (made possible by leveraging [observ](https://github.com/fork-tongue/observ))
* Function components
* Class components with local state and life-cycle methods/hooks
* Single-file components with Vue-like template syntax (`.cgx` files)
* Custom renderers

Here is an example that shows a counter, made with a component with Vue-like syntax:

Contents of `counter.cgx`:
```html
<template>
  <widget>
    <label
      :text="f'Count: {count}'"
    />
    <button
      text="bump"
      @clicked="bump"
    />
  </widget>
</template>

<script>
import collagraph as cg


class Counter(cg.Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state["count"] = 0

    def bump(self):
        self.state["count"] += 1
</script>
```

Contents of `app.py`:
```python
from PySide6 import QtWidgets
import collagraph as cg

# After importing collagraph, it's possible to import
# components directly from .cgx files
from counter import Counter

# Create a Collagraph instance with a PySide renderer
# and register with the Qt event loop
gui = cg.Collagraph(renderer=cg.PySideRenderer())
# Render the component into a container
# (in this case the app but can be another widget)
app = QtWidgets.QApplication()
gui.render(cg.h(Counter), app)
app.exec()
```

Which looks something like this:

![collagraph example](https://github.com/fork-tongue/collagraph/assets/1000968/4ebae92e-d7be-48ea-b76a-c6eab8d62112)

Instead of using a python file as an entry point to run components, you can run them directly using the collagraph CLI:

```sh
poetry run collagraph examples/pyside/counter.cgx
```

For more examples, please take a look at the [examples folder](examples).

Currently there are three renderers:

* [PysideRenderer](collagraph/renderers/pyside_renderer.py): for rendering PySide6 applications
* [PygfxRenderer](collagraph/renderers/pygfx_renderer.py): for rendering 3D graphic scenes with [Pygfx](https://github.com/pygfx/pygfx)
* [DomRenderer](collagraph/renderers/dom_renderer.py): for rendering to browser DOM through [PyScript](https://pyscript.net) (or rather [Pyodide](https://pyodide.org/en/stable/))

It is possible to create a custom Renderer using the [Renderer](collagraph/renderers/__init__.py) interface, to render to other UI frameworks, for instance wxPython.


## Development

To try out Collagraph or start development, run:

```sh
# Basic dev setup (no pygfx or pyside)
poetry install
# Full dev setup
poetry install --with pyside --extras pyside --extras pygfx
# Run example:
poetry run python examples/pyside/layout-example.py
# Run test suite:
poetry run pytest
# Install git pre-commit hooks to make sure tests/linting passes before committing
poetry run pre-commit install
```


### Syntax Highlighting

Syntax highlighting for single-file components (`.cgx`) is supported for VSCode and Sublime Text:

* [CGX syntax highlight for Sublime Text](https://github.com/fork-tongue/cgx-syntax-highlight-sublime)
* [CGX syntax highlight for VSCode](https://github.com/fork-tongue/cgx-syntax-highlight-vscode)


### Formatting and linting

Linting and formatting cgx files is possible with: [ruff-cgx](https://github.com/fork-tongue/ruff-cgx).
