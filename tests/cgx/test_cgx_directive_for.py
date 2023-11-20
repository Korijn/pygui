from observ import reactive

from collagraph.cgx import cgx


def test_directive_for():
    Labels, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <label v-for="label in labels" :text="label" />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Labels(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"labels": []})
    component = Labels(state)
    node = component.render()

    assert node.type == "widget"

    assert len(node.children) == 0

    for labels in (["Foo"], ["Foo", "Bar"], []):
        state["labels"] = labels
        node = component.render()

        assert len(node.children) == len(labels)
        for idx, label in enumerate(labels):
            assert node.children[idx].props["text"] == label


def test_directive_for_with_enumerate():
    Labels, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <label
              v-for="idx, label in enumerate(labels)"
              :key="idx"
              :text="label"
            />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Labels(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"labels": []})
    component = Labels(state)
    node = component.render()

    assert node.type == "widget"

    assert len(node.children) == 0

    for labels in (["Foo"], ["Foo", "Bar"], []):
        state["labels"] = labels
        node = component.render()

        assert len(node.children) == len(labels)
        for idx, label in enumerate(labels):
            assert node.children[idx].props["text"] == label


def test_directive_for_lambdas():
    Example, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <!-- Example of how to capture variables in lambdas in a for-loop -->
            <button
              v-for="name in names"
              :text="name"
              @clicked="lambda ev, name=name: clicked(ev, name)"
            />
            <!-- Alternative way with partial from functools: -->
            <!-- @clicked="partial(lambda ev, name: clicked(ev, name), name=name)" -->
          </widget>
        </template>

        <script>
        import collagraph as cg


        class Example(cg.Component):
            clicked_names = []

            def clicked(self, ev, name):
                Example.clicked_names.append((ev, name))
        </script>
        """
    )

    state = reactive({"names": ["foo", "bar"]})
    component = Example(state)
    node = component.render()

    assert node.type == "widget"

    foo_button, bar_button = node.children

    assert foo_button.props["text"] == "foo"
    assert bar_button.props["text"] == "bar"

    foo_button.props["on_clicked"]("baz")

    assert Example.clicked_names[-1] == ("baz", "foo")

    bar_button.props["on_clicked"]("bas")

    assert Example.clicked_names[-1] == ("bas", "bar")


def test_directive_for_elaborate():
    Labels, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <label
              v-for="idx, (label, suffix) in enumerate(zip(labels, suffixes))"
              :key="idx"
              :text="label"
              :suffix="suffix"
            />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Labels(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"labels": [], "suffixes": []})
    component = Labels(state)
    node = component.render()

    assert node.type == "widget"

    assert len(node.children) == 0

    for labels, suffixes in (
        (["Foo"], ["x"]),
        (["Foo", "Bar"], ["x", "y"]),
        ([], []),
        (["a", "b", "c", "d"], ["1", "2", "3", "4"]),
    ):
        state["labels"] = labels
        state["suffixes"] = suffixes
        node = component.render()

        assert len(node.children) == len(labels)
        for idx, (label, suffix) in enumerate(zip(labels, suffixes)):
            assert node.children[idx].props["text"] == label
            assert node.children[idx].props["suffix"] == suffix


def test_directive_for_nested():
    Labels, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <template
              v-for="y, column in enumerate(rows)"
            >
              <template
                v-for="x, data in enumerate(column)"
              >
                <label :text="f'{x},{y}: {data}'"></label>
              </template>
            </template>
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Labels(cg.Component):
            pass
        </script>
        """
    )

    state = reactive({"rows": [["a", "b", "c"], ["d", "e"]]})
    component = Labels(state)
    node = component.render()

    assert len(node.children) == 2
    assert len(node.children[0].children) == 3
    assert len(node.children[1].children) == 2

    assert node.children[0].children[0].children[0].props["text"] == "0,0: a"
    assert node.children[0].children[1].children[0].props["text"] == "1,0: b"
    assert node.children[0].children[2].children[0].props["text"] == "2,0: c"
    assert node.children[1].children[0].children[0].props["text"] == "0,1: d"
    assert node.children[1].children[1].children[0].props["text"] == "1,1: e"
