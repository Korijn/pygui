import pytest
from observ import reactive

from collagraph import Collagraph, EventLoopType
from collagraph.renderers import DictRenderer
from collagraph.renderers.dict_renderer import format_dict


def test_for_simple(parse_source):
    """
    Render a node with a 1_000 children.
    This ensures that collagraph will not trigger a RecursionError.
    """
    number_of_items = 1_000
    App, _ = parse_source(
        f"""
        <node
          v-for="i in range({number_of_items})"
          :value="i"
        />

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

    assert len(container["children"]) == number_of_items, format_dict(container)
    for idx, child in enumerate(container["children"]):
        assert child["attrs"]["value"] == idx


def test_for_with_children(parse_source):
    values = ["a", "b", "c"]
    App, _ = parse_source(
        f"""
        <node
          v-for="i, text in enumerate({values})"
          :value="i"
        >
          <item :text="text" />
        </node>

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

    assert len(container["children"]) == len(values), format_dict(container)
    for idx, child in enumerate(container["children"]):
        assert child["attrs"]["value"] == idx
        assert child["children"][0]["attrs"]["text"] == values[idx]


def test_for_between_other_tags(parse_source):
    App, _ = parse_source(
        """
        <foo />
        <node
          v-for="i in values"
          :value="i"
        />
        <bar />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    container = {"type": "root"}
    state = reactive({"values": list(range(10))})
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    assert len(container["children"]) == len(state["values"]) + 2
    assert container["children"][0]["type"] == "foo"
    assert container["children"][-1]["type"] == "bar"
    for child in container["children"][1:-1]:
        assert child["type"] == "node"

    state["values"].append(len(state["values"]))

    # Test response to changes in size of v-for
    assert len(container["children"]) == len(state["values"]) + 2
    assert container["children"][0]["type"] == "foo"
    assert container["children"][-1]["type"] == "bar"
    for child in container["children"][1:-1]:
        assert child["type"] == "node"

    state["values"].pop(3)
    state["values"].pop(3)

    assert len(container["children"]) == len(state["values"]) + 2
    assert container["children"][0]["type"] == "foo"
    assert container["children"][-1]["type"] == "bar"
    for child in container["children"][1:-1]:
        assert child["type"] == "node"

    state["values"].clear()

    assert len(container["children"]) == len(state["values"]) + 2
    assert container["children"][0]["type"] == "foo"
    assert container["children"][-1]["type"] == "bar"
    for child in container["children"][1:-1]:
        assert child["type"] == "node"

    state["values"] = [1, 2, 3]

    assert len(container["children"]) == len(state["values"]) + 2
    assert container["children"][0]["type"] == "foo"
    assert container["children"][-1]["type"] == "bar"
    for child in container["children"][1:-1]:
        assert child["type"] == "node"


def test_for_between_if_tags(parse_source):
    App, _ = parse_source(
        """
        <foo v-if="foo" />
        <node
          v-for="i in range(10)"
          :value="i"
        />
        <bar v-if="bar" />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive(
        {
            "foo": False,
            "bar": False,
        }
    )
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    assert len(container["children"]) == 10
    for idx, child in enumerate(container["children"]):
        assert child["attrs"]["value"] == idx

    state["foo"] = True

    assert len(container["children"]) == 11
    assert container["children"][0]["type"] == "foo", format_dict(container)

    state["bar"] = True

    assert len(container["children"]) == 12
    assert container["children"][0]["type"] == "foo"
    assert container["children"][11]["type"] == "bar"


def test_for_simple_reactive(parse_source):
    App, _ = parse_source(
        """
        <node
          v-for="i in items"
          :value="i"
        />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"items": ["a", "b"]})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    items = [child["attrs"]["value"] for child in container["children"]]
    assert items == state["items"], format_dict(container)

    state["items"][1] = "c"

    items = [child["attrs"]["value"] for child in container["children"]]
    assert items == state["items"], format_dict(container)


def test_for_reactive(parse_source):
    App, _ = parse_source(
        """
        <node
          v-for="i in items"
          :value="i"
        />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"items": ["a", "b"]})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    items = [child["attrs"]["value"] for child in container["children"]]
    assert items == state["items"], format_dict(container)

    state["items"].append("c")

    items = [child["attrs"]["value"] for child in container["children"]]
    assert items == state["items"], format_dict(container)

    state["items"].pop(1)

    items = [child["attrs"]["value"] for child in container["children"]]
    assert items == state["items"], format_dict(container)

    state["items"] = ["d", "e"]

    items = [child["attrs"]["value"] for child in container["children"]]
    assert items == state["items"], format_dict(container)


def test_for_reactive_pop(parse_source):
    App, _ = parse_source(
        """
        <before />
        <node
          v-for="i in items"
          :value="i"
        />
        <after />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"items": ["a", "b", "c"]})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    items = [child["attrs"]["value"] for child in container["children"][1:-1]]
    assert items == state["items"], format_dict(container)

    state["items"].pop()

    items = [child["attrs"]["value"] for child in container["children"][1:-1]]
    assert items == state["items"], format_dict(container)


@pytest.mark.xfail
def test_for_keyed(parse_source):
    App, _ = parse_source(
        """
        <node
          v-for="i in items"
          :key="i['id']"
          :text="i['text']"
        />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive(
        {
            "items": [
                {"id": 0, "text": "foo"},
                {"id": 1, "text": "bar"},
            ]
        }
    )
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state)

    assert len(container["children"]) == len(state["items"])
    for node, item in zip(container["children"], state["items"]):
        assert node["type"] == "node"
        assert node["attrs"]["key"] == item["id"]
        assert node["attrs"]["text"] == item["text"]

    state["items"][1]["text"] = "baz"

    assert len(container["children"]) == len(state["items"])
    for node, item in zip(container["children"], state["items"]):
        assert node["type"] == "node"
        assert node["attrs"]["key"] == item["id"]
        assert node["attrs"]["text"] == item["text"]

    assert False, "Figure out how to make sure keyed lists perform better than unkeyed"


def test_example(parse_source):
    App, _ = parse_source(
        """
        <node
          v-for="i, text in enumerate(props['items'])"
          :value="i + 1"
        >
          <item :text="text" :blaat="props['other']" />
        </node>

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"items": ["a", "b", "c"], "other": "toet"})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state)

    assert len(container["children"]) == 3
    assert container["children"][0]["attrs"]["value"] == 1
    assert container["children"][0]["children"][0]["attrs"]["text"] == "a"
    assert container["children"][0]["children"][0]["attrs"]["blaat"] == "toet"


def test_looped_example(parse_source):
    App, _ = parse_source(
        """
        <node
          v-for="i, text in enumerate(props['items'])"
          :value="text"
        >
          <item
            v-for="j, text in enumerate(props['items'])"
            :value="i * len(props['items']) + j"
            :content="text"
          />
        </node>

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"items": ["a", "b", "c"]})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state)

    assert len(container["children"]) == 3
    counter = 0
    for idx, value in enumerate(state["items"]):
        assert container["children"][idx]["attrs"]["value"] == value
        assert len(container["children"][idx]["children"]) == 3
        for child, val in zip(container["children"][idx]["children"], state["items"]):
            assert child["attrs"]["value"] == counter
            assert child["attrs"]["content"] == val
            counter += 1

    state["items"][2] = "d"

    assert len(container["children"]) == 3
    counter = 0
    for idx, value in enumerate(state["items"]):
        assert container["children"][idx]["attrs"]["value"] == value
        assert len(container["children"][idx]["children"]) == 3
        for child, val in zip(container["children"][idx]["children"], state["items"]):
            assert child["attrs"]["value"] == counter
            assert child["attrs"]["content"] == val
            counter += 1


def test_consecutive_lists(parse_source):
    App, _ = parse_source(
        """
        <node_a
          v-for="i, text in enumerate(a)"
          :index="i"
          :text="text"
        />
        <node_b
          v-for="i, text in enumerate(b)"
          :index="i"
          :text="text"
        />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"a": ["a", "b", "c"], "b": ["x", "y", "z"]})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state)

    def assert_consistency():
        assert len(container["children"]) == len(state["a"]) + len(state["b"])
        for idx, value in enumerate(state["a"]):
            assert container["children"][idx]["type"] == "node_a", format_dict(
                container
            )
            assert container["children"][idx]["attrs"]["index"] == idx
            assert container["children"][idx]["attrs"]["text"] == value
        for idx, value in enumerate(state["b"]):
            child_idx = idx + len(state["a"])
            assert container["children"][child_idx]["type"] == "node_b"
            assert container["children"][child_idx]["attrs"]["index"] == idx
            assert (
                container["children"][child_idx]["attrs"]["text"] == value
            ), format_dict(container)

    assert_consistency()

    state["a"].pop()

    assert_consistency()

    state["a"].append("d")

    assert_consistency()

    state["a"][1] = "e"

    assert_consistency()

    state["b"].insert(0, "w")

    assert_consistency()


def test_for_regression(parse_source):
    Counter, namespace = parse_source(
        """
        <counter
          :count="count"
        />
        <script>
        import collagraph as cg
        class Counter(cg.Component):
            pass
        </script>
        """
    )
    Counters, namespace = parse_source(
        """
        <counters>
          <Counter
            v-for="i, prop in enumerate(props['counters'])"
            v-bind="prop"
            :idx="i"
          />
        </counters>

        <script>
        import collagraph as cg

        try:
            import Counter
        except:
            pass

        class Counters(cg.Component):
            pass
        </script>
        """,
        namespace=namespace,
    )
    gui = Collagraph(DictRenderer())
    container = {"type": "root"}
    state = reactive({"counters": [{"count": 0}]})

    gui.render(Counters, container, state=state)

    assert "children" in container["children"][0], format_dict(container)
    assert len(container["children"][0]["children"]) == 1, format_dict(container)
