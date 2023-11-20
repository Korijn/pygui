from collagraph.cgx import cgx


def test_directive_on():
    Buttons, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <!-- Normal on -->
            <button v-on:clicked="increase" text="Add" object_name="add" />
            <!-- Shortcut on -->
            <button @clicked="decrease" text="Sub" object_name="dec" />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Buttons(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state["count"] = 0

            def increase(self):
                self.state["count"] += 1

            def decrease(self):
                self.state["count"] -= 1
        </script>
        """
    )

    component = Buttons({})
    node = component.render()

    add_button = node.children[0]
    sub_button = node.children[1]

    assert component.state["count"] == 0
    assert add_button.props["text"] == "Add"
    assert sub_button.props["text"] == "Sub"

    assert add_button.props["on_clicked"]
    assert sub_button.props["on_clicked"]

    add_button.props["on_clicked"]()

    assert component.state["count"] == 1

    sub_button.props["on_clicked"]()

    assert component.state["count"] == 0
