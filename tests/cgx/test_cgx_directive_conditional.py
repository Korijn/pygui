from observ import reactive

from collagraph.cgx import cgx


def test_directive_if():
    Label, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <label v-if="props['show']" text="Foo" />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Label(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"show": True})
    component = Label(state)
    node = component.render()

    assert node.type == "widget"

    assert len(node.children) == 1
    assert node.children[0].type == "label"
    assert node.children[0].props["text"] == "Foo"

    state["show"] = False
    node = component.render()

    assert len(node.children) == 0


def test_directive_if_elaborate():
    Label, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <label v-if="props['show']" text="Foo" />
            <label text="Bar" />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Label(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"show": True})
    component = Label(state)
    node = component.render()

    assert node.type == "widget"

    assert len(node.children) == 2
    assert node.children[0].type == "label"
    assert node.children[0].props["text"] == "Foo"
    assert node.children[1].props["text"] == "Bar"

    state["show"] = False
    node = component.render()

    assert len(node.children) == 1

    assert node.children[0].props["text"] == "Bar"


def test_directive_else():
    Label, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <label v-if="props['show']" text="Foo" />
            <label v-else text="Bar" />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Label(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"show": True})
    component = Label(state)
    node = component.render()

    assert node.type == "widget"

    assert len(node.children) == 1
    assert node.children[0].type == "label"
    assert node.children[0].props["text"] == "Foo"

    state["show"] = False
    node = component.render()

    assert len(node.children) == 1
    assert node.children[0].type == "label"
    assert node.children[0].props["text"] == "Bar"


def test_directive_else_if():
    Label, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <label v-if="props['foo']" text="Foo" />
            <label v-else-if="props['bar']" text="Bar" />
            <label v-else-if="props['baz']" text="Baz" />
            <label v-else text="Bas" />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Label(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"foo": True, "bar": True, "baz": True})
    component = Label(state)
    node = component.render()

    assert node.type == "widget"

    assert len(node.children) == 1
    assert node.children[0].type == "label"
    assert node.children[0].props["text"] == "Foo"

    state["foo"] = False
    node = component.render()

    assert len(node.children) == 1
    assert node.children[0].type == "label"
    assert node.children[0].props["text"] == "Bar"

    state["bar"] = False
    node = component.render()

    assert len(node.children) == 1
    assert node.children[0].type == "label"
    assert node.children[0].props["text"] == "Baz"

    state["baz"] = False
    node = component.render()

    assert len(node.children) == 1
    assert node.children[0].type == "label"
    assert node.children[0].props["text"] == "Bas"
