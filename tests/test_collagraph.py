import pytest
from observ import reactive

from collagraph import Collagraph, EventLoopType
from collagraph.renderers import DictRenderer


def test_basic_dict_renderer(parse_source):
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

    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    container = {"type": "root"}
    gui.render(App, container)

    assert container["children"][0] == {"type": "app"}


def test_renderer_required():
    # renderer argument is required
    with pytest.raises(TypeError):
        Collagraph(event_loop_type=EventLoopType.SYNC)

    # When the renderer argument is passed, it should be a Renderer subclass
    with pytest.raises(TypeError) as e:
        Collagraph(
            renderer=True,
            event_loop_type=EventLoopType.SYNC,
        )

    assert "Expected a Renderer" in str(e)


def test_reactive_element(parse_source):
    App, _ = parse_source(
        """
        <counter
          :count="count"
        />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    container = {"type": "root"}
    state = reactive({"count": 0})

    gui.render(App, container, state)

    counter = container["children"][0]
    assert counter["type"] == "counter"
    assert counter["attrs"]["count"] == 0

    # Update state, which should trigger a re-render
    state["count"] += 1

    assert counter["attrs"]["count"] == 1, counter


def test_lots_of_elements(parse_source):
    """Render a node with a 1000 children.
    This test makes sure that `collagraph` will not trigger any RecursionError.
    """
    App, _ = parse_source(
        """
        <app>
          <node v-for="i in range(10000)" />
        </app>

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )
    gui = Collagraph(renderer=DictRenderer(), event_loop_type=EventLoopType.SYNC)
    container = {"type": "root"}
    gui.render(App, container)

    assert len(container["children"][0]["children"]) == 10000


def test_delete_item_with_children_and_siblings(parse_source, process_events):
    Item, namespace = parse_source(
        """
        <item>
          <part v-for="title in parts" :title="title" />
        </item>

        <script>
        import collagraph as cg

        class Item(cg.Component):
            pass
        </script>
        """
    )

    Collection, _ = parse_source(
        """
        <collection>
          <Item v-for="part in items" v-bind="part" />
        </collection>

        <script>
        import collagraph as cg
        try:
            import Item
        except ImportError:
            pass

        class Collection(cg.Component):
            pass
        </script>
        """,
        namespace=namespace,
    )

    gui = Collagraph(renderer=DictRenderer(), event_loop_type=EventLoopType.DEFAULT)
    container = {"type": "root"}
    state = reactive(
        {
            "items": [
                {"parts": ["a"]},
                {"parts": ["b", "c"]},
                {"parts": ["d"]},
            ]
        }
    )

    gui.render(Collection, container, state=state)

    process_events()

    collection = container["children"][0]
    assert len(collection["children"]) == 3
    assert len(collection["children"][1]["children"]) == 2
    assert collection["children"][1]["children"][1]["type"] == "part"
    assert collection["children"][1]["children"][1]["attrs"]["title"] == "c"

    # Trigger a deletion *and* a change to the sibling for instance
    state["items"].pop(1)
    state["items"][1]["parts"][0] = "e"

    process_events()

    # TODO: check that there was only one dom update cycle needed for
    # the batched changes

    assert len(collection["children"]) == 2
    assert collection["children"][1]["children"][0]["type"] == "part"
    assert collection["children"][1]["children"][0]["attrs"]["title"] == "e"
