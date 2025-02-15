from observ import reactive

from collagraph import Collagraph, EventLoopType
from collagraph.renderers import DictRenderer


def test_component_tag(parse_source):
    App, _ = parse_source(
        """
        <SubComponent />

        <script>
        import collagraph as cg


        class SubComponent(cg.Component):
            def render(self, renderer):
                from collagraph.fragment import (
                    ControlFlowFragment,
                    ComponentFragment,
                    ListFragment,
                    Fragment,
                )

                component = ComponentFragment(renderer)
                sub0 = Fragment(renderer, tag="sub", parent=component)
                return component


        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"foo": "foo"})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    assert len(container["children"]) == 1
    assert container["children"][0]["type"] == "sub", container


def test_component_tag_props_and_events(parse_source):
    SubComponent, namespace = parse_source(
        """
        <sub
          :subval="val"
          :subvalue="value"
          :subother="other"
          @subaction="lambda: emit('action')"
        />

        <script>
        import collagraph as cg
        class SubComponent(cg.Component):
            pass
        </script>
        """
    )

    App, namespace = parse_source(
        """
        <el
          :count="action_count"
        >
          <SubComponent
            val="foo"
            :value="bar"
            :other="baz"
            @action="bump"
          />
        </el>

        <script>
        import collagraph as cg

        try:
            import SubComponent
        except:
            pass

        class App(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["action_count"] = 0

            def bump(self):
                self.state["action_count"] += 1
        </script>
        """,
        namespace=namespace,
    )

    state = reactive({"bar": "foo", "baz": "baz"})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    assert len(container["children"]) == 1
    el = container["children"][0]
    assert el["type"] == "el"
    assert len(el["children"]) == 1
    sub = el["children"][0]
    assert sub["type"] == "sub"
    assert sub["attrs"]["subval"] == "foo"
    assert sub["attrs"]["subvalue"] == "foo"
    assert sub["attrs"]["subother"] == "baz"

    state["bar"] = "bar"

    assert sub["attrs"]["subvalue"] == "bar"

    state["baz"] = "blaat"

    assert sub["attrs"]["subother"] == "blaat"

    # Check that events work
    assert el["attrs"]["count"] == 0
    assert "subaction" in sub["handlers"], sub["handlers"]
    for handler in sub["handlers"]["subaction"]:
        handler()

    assert el["attrs"]["count"] == 1
