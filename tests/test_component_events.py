import collagraph as cg


def test_components_events():
    from tests.data.component.events_parent import Parent

    gui = cg.Collagraph(
        cg.DictRenderer(),
        event_loop_type=cg.EventLoopType.SYNC,
    )
    container = {"type": "root"}
    gui.render(Parent, container)

    parent_dom = container["children"][0]
    child_dom = parent_dom["children"][0]

    assert parent_dom["type"] == "parent"
    assert child_dom["type"] == "child"
    assert parent_dom["attrs"]["count"] == 0
    assert child_dom["attrs"]["value"] == "foo"
    assert "simple_event" in child_dom["handlers"]

    for handler in child_dom["handlers"]["simple_event"]:
        handler()

    assert parent_dom["attrs"]["count"] == 1

    for handler in child_dom["handlers"]["event_with_arg"]:
        handler()

    assert parent_dom["attrs"]["count"] == 5
