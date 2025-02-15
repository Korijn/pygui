import pytest
from observ import reactive

from collagraph import Collagraph, EventLoopType
from collagraph.renderers import DictRenderer
from collagraph.renderers.dict_renderer import format_dict


def test_slots_dynamic_if_template():
    from tests.data.slots.dynamic_if_template import Tree

    state = reactive({"show_content": False})

    gui = Collagraph(DictRenderer(), event_loop_type=EventLoopType.SYNC)
    container = {"type": "container"}
    gui.render(Tree, container, state)

    root = container["children"][0]
    assert root["type"] == "node"
    assert "children" not in root

    state["show_content"] = True

    assert "children" in root, format_dict(root)
    assert len(root["children"]) == 1, format_dict(root)

    state["show_content"] = False

    assert "children" not in root, format_dict


def test_slots_dynamic_for_template():
    from tests.data.slots.dynamic_for_template import Tree

    state = reactive({"content": ["a", "b"]})

    gui = Collagraph(DictRenderer(), event_loop_type=EventLoopType.SYNC)
    container = {"type": "container"}
    gui.render(Tree, container, state)

    root = container["children"][0]
    assert root["type"] == "node"
    assert "children" in root
    assert len(root["children"]) == 2

    state["content"].append("c")

    assert len(root["children"]) == 3, format_dict(root)

    state["content"].remove("a")

    assert len(root["children"]) == 2, format_dict(root)

    state["content"] = []

    assert "children" not in root, format_dict(root)


@pytest.mark.xfail
def test_slots_dynamic_if():
    from tests.data.slots.dynamic_if import Tree

    state = reactive({"show_content": False})

    gui = Collagraph(DictRenderer(), event_loop_type=EventLoopType.SYNC)
    container = {"type": "container"}
    gui.render(Tree, container, state)

    root = container["children"][0]
    assert root["type"] == "node"
    assert "children" not in root

    state["show_content"] = True

    assert "children" in root, format_dict(root)
    assert len(root["children"]) == 1, format_dict(root)

    state["show_content"] = False

    assert "children" not in root, format_dict


@pytest.mark.xfail
def test_slots_dynamic_for():
    from tests.data.slots.dynamic_for import Tree

    state = reactive({"content": ["a", "b"]})

    gui = Collagraph(DictRenderer(), event_loop_type=EventLoopType.SYNC)
    container = {"type": "container"}
    gui.render(Tree, container, state)

    root = container["children"][0]
    assert root["type"] == "node"
    assert "children" in root
    assert len(root["children"]) == 2

    state["content"].append("c")

    assert len(root["children"]) == 3, format_dict(root)

    state["content"].remove("a")

    assert len(root["children"]) == 2, format_dict(root)

    state["content"] = []

    assert "children" not in root, format_dict(root)
