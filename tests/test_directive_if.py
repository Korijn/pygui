from observ import reactive

from collagraph import Collagraph, EventLoopType
from collagraph.renderers import DictRenderer


def test_directive_if_root(parse_source):
    App, _ = parse_source(
        """
        <app v-if="foo" />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"foo": False})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    assert "children" not in container

    state["foo"] = True

    assert len(container["children"]) == 1
    assert container["children"][0]["type"] == "app"

    state["foo"] = False

    assert "children" not in container

    state["foo"] = True

    assert len(container["children"]) == 1
    assert container["children"][0]["type"] == "app"


def test_directive_if_non_root(parse_source):
    App, _ = parse_source(
        """
        <app>
          <item v-if="foo" />
        </app>

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"foo": False})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    app = container["children"][0]
    assert app["type"] == "app"
    assert "children" not in app

    state["foo"] = True

    assert len(app["children"]) == 1
    assert app["children"][0]["type"] == "item"

    state["foo"] = False

    assert "children" not in app

    state["foo"] = True

    assert len(app["children"]) == 1
    assert app["children"][0]["type"] == "item"


def test_directive_if_with_children(parse_source):
    App, _ = parse_source(
        """
        <app v-if="foo">
          <item text="foo" />
        </app>

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"foo": False})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    assert "children" not in container

    state["foo"] = True

    app = container["children"][0]
    assert app["type"] == "app"
    assert len(app["children"]) == 1
    assert app["children"][0]["type"] == "item"
    assert app["children"][0]["attrs"]["text"] == "foo"

    state["foo"] = False

    assert "children" not in container

    state["foo"] = True

    app = container["children"][0]
    assert app["type"] == "app"
    assert len(app["children"]) == 1
    assert app["children"][0]["type"] == "item"
    assert app["children"][0]["attrs"]["text"] == "foo"


def test_directive_if_surrounded(parse_source):
    App, _ = parse_source(
        """
        <before />
        <app v-if="foo" />
        <after />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"foo": False})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    assert len(container["children"]) == 2
    assert container["children"][0]["type"] == "before"
    assert container["children"][-1]["type"] == "after"

    state["foo"] = True

    assert len(container["children"]) == 3
    assert container["children"][1]["type"] == "app"
    assert container["children"][0]["type"] == "before"
    assert container["children"][-1]["type"] == "after"

    state["foo"] = False

    assert len(container["children"]) == 2
    assert container["children"][0]["type"] == "before"
    assert container["children"][-1]["type"] == "after"

    state["foo"] = True

    assert len(container["children"]) == 3
    assert container["children"][1]["type"] == "app"
    assert container["children"][0]["type"] == "before"
    assert container["children"][-1]["type"] == "after"


def test_directive_if_nested_if(parse_source):
    App, _ = parse_source(
        """
        <app v-if="foo">
          <item v-if="bar" />
        </app>

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"foo": False, "bar": False})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    assert "children" not in container

    state["foo"] = True

    app = container["children"][0]
    assert app["type"] == "app"
    assert "children" not in app

    state["bar"] = True

    assert len(app["children"]) == 1
    assert app["children"][0]["type"] == "item"

    state["foo"] = False

    assert "children" not in app

    state["foo"] = True

    assert len(container["children"]) == 1
    app = container["children"][0]
    assert app["type"] == "app"
    assert app["children"][0]["type"] == "item"

    state["bar"] = False

    app = container["children"][0]
    assert app["type"] == "app"
    assert "children" not in app


def test_directive_if_nested_for(parse_source):
    App, _ = parse_source(
        """
        <app v-if="foo">
          <item
            v-for="name in names"
            :text="name"
          />
        </app>

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"foo": True, "names": ["a", "b"]})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    app = container["children"][0]
    assert app["type"] == "app"
    assert len(app["children"]) == 2
    for child, name in zip(app["children"], state["names"]):
        assert child["attrs"]["text"] == name

    state["names"].append("c")

    assert len(app["children"]) == 3
    for child, name in zip(app["children"], state["names"]):
        assert child["attrs"]["text"] == name

    state["foo"] = False

    assert "children" not in container

    state["foo"] = True

    app = container["children"][0]
    assert "children" in app
    assert app["type"] == "app"
    assert len(app["children"]) == 3
    for child, name in zip(app["children"], state["names"]):
        assert child["attrs"]["text"] == name
