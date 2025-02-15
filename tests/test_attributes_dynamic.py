from copy import deepcopy

import pytest
from observ import reactive

from collagraph import Collagraph, EventLoopType, __version__
from collagraph.renderers import DictRenderer


def test_dynamic_attribute_object_method(parse_source):
    App, _ = parse_source(
        """
        <app v-bind:foo="bar()" />

        <script>
        import collagraph as cg

        class App(cg.Component):
            def bar(self):
                return "baz"
        </script>
        """
    )

    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container)

    app = container["children"][0]
    assert app["attrs"]["foo"] == "baz"


def test_dynamic_attribute_object_property(parse_source):
    App, _ = parse_source(
        """
        <app :foo="bar" />

        <script>
        import collagraph as cg

        class App(cg.Component):
            def __init__(self, props):
                super().__init__(props)
                self.bar = "baz"
        </script>
        """
    )

    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container)

    app = container["children"][0]
    assert app["attrs"]["foo"] == "baz"


def test_dynamic_attribute_module_scope(parse_source):
    App, _ = parse_source(
        """
        <app :foo="bar" />

        <script>
        import collagraph as cg

        bar = "baz"

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

    app = container["children"][0]
    assert app["attrs"]["foo"] == "baz"


def test_dynamic_attribute_state(parse_source):
    App, _ = parse_source(
        """
        <app :foo="bar" />

        <script>
        import collagraph as cg

        class App(cg.Component):
            def __init__(self, props):
                super().__init__(props)
                self.state["bar"] = "baz"
        </script>
        """
    )

    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container)

    app = container["children"][0]
    assert app["attrs"]["foo"] == "baz"


def test_dynamic_attribute_props(parse_source):
    App, _ = parse_source(
        """
        <app :foo="bar" />

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
    gui.render(App, container, state={"bar": "baz"})

    app = container["children"][0]
    assert app["attrs"]["foo"] == "baz"


def test_dynamic_attribute_props_change(parse_source):
    App, _ = parse_source(
        """
        <app :foo="bar" />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"bar": "baz"})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    app = container["children"][0]
    assert app["attrs"]["foo"] == "baz"

    state["bar"] = "bam"

    assert app["attrs"]["foo"] == "bam"


def test_dynamic_attribute_basic_dict(parse_source):
    Labels, _ = parse_source(
        """
        <!-- Bind with complete dictionary -->
        <widget :layout="{'type': 'box', 'direction': Direction.LeftToRight}">
          <!-- Normal bind -->
          <label v-bind:text="state['label_text']"/>
          <!-- Use context -->
          <label :text="cg.__version__"/>
        </widget>

        <script>
        from enum import Enum
        import collagraph as cg


        class Direction(Enum):
            LeftToRight = 0
            RightToLeft = 1


        class Labels(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["label_text"] = self.props.get("text", "Label")
        </script>
        """
    )

    state = reactive({"values": {"foo": "foo"}})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(Labels, container, state=state)

    node = container["children"][0]

    assert node["type"] == "widget"
    assert node["attrs"]["layout"]
    assert node["attrs"]["layout"]["type"] == "box"
    assert node["attrs"]["layout"]["direction"].value == 0

    first_label = node["children"][0]
    second_label = node["children"][1]

    assert first_label["attrs"]["text"] == "Label"
    assert second_label["attrs"]["text"] == __version__



def test_dynamic_attribute_dict(parse_source):
    App, _ = parse_source(
        """
        <app v-bind="values" />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"values": {"foo": "foo"}})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    app = container["children"][0]
    assert app["attrs"]["foo"] == "foo", app

    # Change initial attribute
    state["values"]["foo"] = "bar"

    assert app["attrs"]["foo"] == "bar"

    # Add additional attribute
    state["values"]["bar"] = "bar"

    assert app["attrs"]["foo"] == "bar"
    assert app["attrs"]["bar"] == "bar"

    # Change the added attribute
    state["values"]["bar"] = "baz"

    assert app["attrs"]["bar"] == "baz"

    # Delete the initial attribute
    del state["values"]["foo"]

    assert "foo" not in app["attrs"]


def test_dynamic_attribute_deep(parse_source):
    App, _ = parse_source(
        """
        <app :values="values" />

        <script>
        import collagraph as cg

        class App(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"values": {"foo": "foo"}})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(App, container, state=state)

    app = container["children"][0]
    assert app["attrs"]["values"] == {"foo": "foo"}, app

    # Now override the value for 'values' with a deepcopy of the original value
    app["attrs"]["values"] = deepcopy(app["attrs"]["values"])

    # Change initial attribute
    state["values"]["foo"] = "bar"

    assert app["attrs"]["values"] == {"foo": "bar"}


def test_dynamic_attribute_full(parse_source):
    Labels, _ = parse_source(
        """
        <widget>
          <!-- Bind multiple attributes -->
          <label v-bind="props"/>
          <!-- Multiple bind before (text is set to 'other' text) -->
          <label v-bind="props" :text="other" />
          <!-- Multiple bind after (text is set to props['text'] -->
          <label :text="other" v-bind="props" />
        </widget>

        <script>
        import collagraph as cg

        class Labels(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["other"] = "bar"
        </script>
        """
    )

    state = reactive({"text": "foo", "other": "bar", "extra": "baz"})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    gui.render(Labels, container, state=state)

    node = container["children"][0]

    assert node["type"] == "widget"

    first_label, second_label, third_label = node["children"]

    assert first_label["attrs"]["text"] == "foo"
    assert second_label["attrs"]["text"] == "bar"
    assert third_label["attrs"]["text"] == "foo"
    assert first_label["attrs"]["extra"] == "baz"

    del state["extra"]

    assert "extra" not in first_label["attrs"]


def test_dynamic_attribute_typo(parse_source):
    App, _ = parse_source(
        """
        <widget>
          <!-- stat instead of state -->
          <label :text="stat['text']"/>
        </widget>

        <script>
        import collagraph as cg

        class App(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["text"] = "Foo"
        </script>
        """
    )

    state = reactive({"values": {"foo": "foo"}})
    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )
    with pytest.raises(NameError):
        gui.render(App, container, state=state)

