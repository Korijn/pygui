import pytest


import collagraph as cg
from collagraph.cgx import cgx


def test_directive_bind():
    Labels, _ = cgx.load_from_string(
        """
        <template>
          <widget>
              <!-- Normal bind -->
              <label v-bind:text="state['label_text']"/>
              <!-- Shortcut for bind -->
              <label :text="props['text']"/>
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Labels(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["label_text"] = self.props.get("text", "Label")
        </script>
        """
    )

    component = Labels({"text": "Custom label"})
    node = component.render()

    assert node.type == "widget"

    first_label = node.children[0]
    second_label = node.children[1]

    assert first_label.props["text"] == "Custom label"
    assert second_label.props["text"] == "Custom label"


def test_directive_typo():
    # Would be most excellent if the typo could already
    # be detected at import, but that can only work if
    # the component can define all props and state...
    Label, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <!-- stat instead of state -->
            <label :text="stat['text']"/>
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Label(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["text"] = "Foo"
        </script>
        """
    )

    component = Label({})
    with pytest.raises(NameError):
        component.render()


def test_directive_bind_context():
    Labels, _ = cgx.load_from_string(
        """
        <template>
          <!-- Bind with complete dictionary -->
          <widget :layout="{'type': 'box', 'direction': Direction.LeftToRight}">
            <!-- Normal bind -->
            <label v-bind:text="state['label_text']"/>
            <!-- Use context -->
            <label :text="cg.__version__"/>
          </widget>
        </template>

        <script lang="python">
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

    component = Labels({})
    node = component.render()

    assert node.type == "widget"
    assert node.props["layout"]
    assert node.props["layout"]["type"] == "box"
    assert node.props["layout"]["direction"].value == 0

    first_label = node.children[0]
    second_label = node.children[1]

    assert first_label.props["text"] == "Label"
    assert second_label.props["text"] == cg.__version__


def test_directive_bind_state_and_props():
    Labels, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <!-- Bind to item from self.state  -->
            <label :text="label_text"/>
            <!-- Bind to item from self.props -->
            <label :text="text"/>
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Labels(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["label_text"] = self.props["text"]
        </script>
        """
    )

    component = Labels({"text": "Custom label"})
    node = component.render()

    assert node.type == "widget"

    first_label = node.children[0]
    second_label = node.children[1]

    assert first_label.props["text"] == "Custom label"
    assert second_label.props["text"] == "Custom label"


def test_directive_bind_full():
    Labels, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <!-- Bind multiple attributes -->
            <label v-bind="props"/>
            <!-- Multiple bind before (text is set to 'other' text) -->
            <label v-bind="props" :text="other" />
            <!-- Multiple bind after (text is set to props['text'] -->
            <label :text="other" v-bind="props" />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Labels(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["other"] = "bar"
        </script>
        """
    )

    component = Labels({"text": "foo", "other": "bar"})
    node = component.render()

    assert node.type == "widget"

    first_label = node.children[0]
    second_label = node.children[1]
    third_label = node.children[2]

    assert first_label.props["text"] == "foo"
    assert second_label.props["text"] == "bar"
    assert third_label.props["text"] == "foo"
