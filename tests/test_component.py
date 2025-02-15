import pytest
from observ import reactive
from observ.traps import ReadonlyError

import collagraph as cg


def test_component_without_render_method():
    class Faulty(cg.Component):
        pass

    gui = cg.Collagraph(cg.DictRenderer(), event_loop_type=cg.EventLoopType.SYNC)
    container = {"type": "root"}

    with pytest.raises(NotImplementedError):
        gui.render(Faulty, container)


@pytest.mark.parametrize("attr", ["props", "state", "element", "parent"])
def test_component_no_override(parse_source, attr):
    Item, _ = parse_source(
        f"""
        <item />

        <script>
        import collagraph as cg

        class Item(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.{attr} = {{}}
        </script>
        """
    )

    gui = cg.Collagraph(cg.DictRenderer(), event_loop_type=cg.EventLoopType.SYNC)
    container = {"type": "root"}

    with pytest.raises(RuntimeError):
        gui.render(Item, container)


def test_component_props_read_only(parse_source):
    Item, _ = parse_source(
        """
        <item />

        <script>
        import collagraph as cg

        class Item(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.props["foo"] = "bar"
        </script>
        """
    )

    gui = cg.Collagraph(cg.DictRenderer(), event_loop_type=cg.EventLoopType.SYNC)
    container = {"type": "root"}

    with pytest.raises(ReadonlyError):
        gui.render(Item, container)


def test_component_parent(parse_source):
    Child, namespace = parse_source(
        """
        <child />

        <script>
        import collagraph as cg

        class Child(cg.Component):
            parent_instance = None

            def mounted(self):
                Child.parent_instance = self.parent
        </script>
        """
    )

    Parent, namespace = parse_source(
        """
        <parent>
          <Child />
        </parent>

        <script>
        import collagraph as cg
        try:
            import Child
        except ImportError:
            pass

        class Parent(cg.Component):
            pass
        </script>
        """,
        namespace=namespace,
    )

    gui = cg.Collagraph(cg.DictRenderer(), event_loop_type=cg.EventLoopType.SYNC)
    container = {"type": "root"}
    gui.render(Parent, container)

    assert Child.parent_instance is not None
    assert isinstance(Child.parent_instance, Parent)


def test_component_callback(parse_source):
    Counter, _ = parse_source(
        """
        <script>
        import collagraph as cg

        class Counter(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["count"] = self.props.get("count", 0)
                self.state["step_size"] = self.props.get("step_size", 1)

            def bump(self):
                self.state["count"] += self.state["step_size"]
        </script>

        <counter :count="state['count']" @bump="bump" />
        """
    )
    gui = cg.Collagraph(cg.DictRenderer(), event_loop_type=cg.EventLoopType.SYNC)
    container = {"type": "root"}
    state = reactive({"count": 0})
    gui.render(Counter, container, state=state)

    counter = container["children"][0]
    assert counter["type"] == "counter"
    assert counter["attrs"]["count"] == 0

    for i in range(1, 6):
        # Update state by triggering all listeners, which should trigger a re-render
        for listener in counter["handlers"]["bump"]:
            listener()

        assert counter["attrs"]["count"] == i

    # Assert that global state hasn't been touched
    assert state["count"] == 0


def test_component_element(parse_source):
    Example, _ = parse_source(
        """
        <el />

        <script>
        import collagraph as cg

        class Example(cg.Component):
            component = None

            def mounted(self):
                Example.component = self
        </script>
        """
    )

    gui = cg.Collagraph(cg.DictRenderer(), event_loop_type=cg.EventLoopType.SYNC)
    container = {"type": "root"}
    state = reactive({"count": 0})
    gui.render(Example, container, state=state)

    assert Example.component is not None
    assert isinstance(Example.component, Example)
    assert Example.component.element is container["children"][0]
