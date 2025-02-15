from collagraph import Collagraph, EventLoopType
from collagraph.renderers import DictRenderer


def test_simple_tree(parse_source):
    App, _ = parse_source(
        """
        <app/>

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container)

    assert container["children"][0] == {"type": "app"}


def test_hierarchical_tree(parse_source):
    App, _ = parse_source(
        """
        <parent>
          <child />
          <child>
            <grand-child />
            <grand-child />
          </child>
        </parent>

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container)

    assert container["children"][0]["type"] == "parent"
    assert len(container["children"][0]["children"]) == 2
    for child in container["children"][0]["children"]:
        assert child["type"] == "child"
    assert len(container["children"][0]["children"][1]["children"])
    for grand_child in container["children"][0]["children"][1]["children"]:
        assert grand_child["type"] == "grand-child"


def test_tree_with_multiple_roots(parse_source):
    App, _ = parse_source(
        """
        <item />
        <other />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container)

    assert len(container["children"]) == 2
    assert container["children"][0]["type"] == "item"
    assert container["children"][1]["type"] == "other"


def test_items_with_dashes(parse_source):
    App, _ = parse_source(
        """
        <dashed-item :name="props.get('name')" />

        <script>
        import collagraph as cg
        class App(cg.Component):
            pass
        </script>
        """
    )

    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container)

    assert len(container["children"]) == 1
    assert container["children"][0]["type"] == "dashed-item"
