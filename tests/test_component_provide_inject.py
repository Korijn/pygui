from collagraph import Collagraph, DictRenderer, EventLoopType


def test_component_provide_inject():
    from tests.data.component.provide_parent import Parent

    gui = Collagraph(DictRenderer(), event_loop_type=EventLoopType.SYNC)
    container = {"type": "root"}
    gui.render(Parent, container)

    parent = container["children"][0]
    child = parent["children"][0]
    assert child["attrs"]["injected_default"] == "bar"
    assert child["attrs"]["injected_value"] == "foo"
    assert child["attrs"]["injected_non_existing"] is None


def test_component_provide_inject_deep():
    from tests.data.component.provide_root import Root

    gui = Collagraph(DictRenderer(), event_loop_type=EventLoopType.SYNC)
    container = {"type": "root"}
    gui.render(Root, container)

    root = container["children"][0]
    parent = root["children"][0]
    child = parent["children"][0]
    assert child["attrs"]["injected_default"] == "baz"
    assert child["attrs"]["injected_value"] == "foo"
    assert child["attrs"]["injected_non_existing"] is None
