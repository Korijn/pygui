import importlib
import warnings
from types import ModuleType

import pytest
from observ import reactive

import collagraph as cg
from collagraph.sfc import compiler


def test_warn_on_shadow_import():
    compiler.CGX_RUNTIME_WARNINGS = True

    import tests.data.shadow_imports

    # The module might have already been imported, so
    # in order to make sure that the generated code has
    # no runtime warnings in it, it needs to be reloaded
    importlib.reload(tests.data.shadow_imports)

    state = reactive({"tests": "baz"})

    gui = cg.Collagraph(
        renderer=cg.DictRenderer(),
        event_loop_type=cg.EventLoopType.SYNC,
    )
    container = {"type": "container"}
    with pytest.warns(UserWarning) as records:
        gui.render(tests.data.shadow_imports.Example, container, state=state)

    result = container['children'][0]

    assert len(records) == 3

    assert result["type"] == "widget"
    assert result["attrs"]["data"] != "foo"
    assert result["attrs"]["data"] != "bar"
    assert result["attrs"]["data"] != "baz"
    assert isinstance(result["attrs"]["data"], ModuleType)


def test_disable_warnings():
    compiler.CGX_RUNTIME_WARNINGS = False

    import tests.data.shadow_imports

    # The module might have already been imported, so
    # in order to make sure that the generated code has
    # no runtime warnings in it, it needs to be reloaded
    importlib.reload(tests.data.shadow_imports)

    state = reactive({"tests": "bar"})

    gui = cg.Collagraph(
        renderer=cg.DictRenderer(),
        event_loop_type=cg.EventLoopType.SYNC,
    )
    container = {"type": "container"}

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        gui.render(tests.data.shadow_imports.Example, container, state=state)
