import pytest
from observ import reactive

from collagraph import Collagraph, DictRenderer, EventLoopType
from collagraph.renderers.dict_renderer import format_dict


@pytest.mark.xfail
def test_text_elements():
    from tests.data.text.expressions import Example

    state = reactive({"content": "foo", "more": "bar"})

    gui = Collagraph(DictRenderer(), event_loop_type=EventLoopType.SYNC)
    container = {"type": "container"}
    gui.render(Example, container, state)

    result = container["children"][0]

    assert result["type"] == "div"

    static_p, dynamic_p, multiple_p, split_p = result["children"]

    assert static_p["type"] == "p"
    assert dynamic_p["type"] == "p"
    assert multiple_p["type"] == "p"
    assert split_p["type"] == "p"

    assert (
        "children" in static_p and "children" in dynamic_p and "children" in multiple_p
    ), format_dict(container)

    assert (
        len(static_p["children"])
        == len(dynamic_p["children"])
        == len(multiple_p["children"])
        == 1
    ), format_dict(container)

    static, dynamic, multiple = (
        static_p["children"][0],
        dynamic_p["children"][0],
        multiple_p["children"][0],
    )
    assert static["type"] == "TEXT_ELEMENT"
    assert dynamic["type"] == "TEXT_ELEMENT"
    assert multiple["type"] == "TEXT_ELEMENT"
    assert static["attrs"]["content"] == "Static content"
    assert dynamic["attrs"]["content"] == "Dynamic foo"
    assert multiple["attrs"]["content"] == r"Even bar dyna{}mic\{} foo"

    assert len(split_p["children"]) == 4
    assert split_p["children"][0]["type"] == "TEXT_ELEMENT"
    assert split_p["children"][1]["type"] == "TEXT_ELEMENT"
    assert split_p["children"][2]["type"] == "span"
    assert split_p["children"][3]["type"] == "TEXT_ELEMENT"
    assert split_p["children"][0]["attrs"]["content"] == "Split"
    assert split_p["children"][1]["attrs"]["content"] == " and split by "
    assert split_p["children"][3]["attrs"]["content"] == " element"
