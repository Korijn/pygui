from observ import reactive

import collagraph as cg


def test_resolve_names(parse_source):
    Example, _ = parse_source(
        """
        <root>
          <!-- Test for binding props['prop_val'] -->
          <item :value="prop_val" />
          <!-- Test for binding state['state_val'] -->
          <item :value="state_val" />
          <!-- Test for binding self.val -->
          <item :value="val" />

          <!-- Test for v-if props['prop_val'] -->
          <item v-if="prop_val" :value="prop_val" />
          <!-- Test for v-if state['state_val'] -->
          <item v-if="state_val" :value="state_val" />
          <!-- Test for v-if self.val -->
          <item v-if="val" :value="val" />
        </root>

        <script>
        import collagraph as cg

        class Example(cg.Component):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                assert "prop_val" in self.props
                self.state["state_val"] = "state_value"

            @property
            def val(self):
                return "value"
        </script>
        """
    )

    state = reactive({"prop_val": "prop_value"})

    gui = cg.Collagraph(
        renderer=cg.DictRenderer(),
        event_loop_type=cg.EventLoopType.SYNC,
    )
    container = {"type": "container"}
    gui.render(Example, container, state=state)

    root = container["children"][0]

    item = root["children"][0]
    assert item["attrs"]["value"] == "prop_value", item
    item = root["children"][1]
    assert item["attrs"]["value"] == "state_value", item
    item = root["children"][2]
    assert item["attrs"]["value"] == "value", item

    item = root["children"][3]
    assert item["attrs"]["value"] == "prop_value", item
    item = root["children"][4]
    assert item["attrs"]["value"] == "state_value", item
    item = root["children"][5]
    assert item["attrs"]["value"] == "value", item


def test_file_dunder():
    from tests.data.file_dunder import Example

    gui = cg.Collagraph(
        renderer=cg.DictRenderer(),
        event_loop_type=cg.EventLoopType.SYNC,
    )
    container = {"type": "container"}
    gui.render(Example, container)

    example = Example()
    file = example.file()

    assert file.endswith("file_dunder.cgx")

    name = example.name()
    assert name.endswith("file_dunder")

    package = example.package()
    assert package == "tests.data"
