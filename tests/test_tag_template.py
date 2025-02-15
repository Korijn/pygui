from observ import reactive

from collagraph import Collagraph, EventLoopType
from collagraph.renderers import DictRenderer


def test_tag_template(parse_source):
    App, _ = parse_source(
        """
        <template>
          <foo />
        </template>

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
    assert container["children"][0]["type"] == "foo"

    App = None
    _ = None
    container = None
    gui = None


def test_component_template_tag(parse_source):
    Template, _ = parse_source(
        """
        <template>
          <content>
            <template>
              <child name="a" />
              <child name="b" />
            </template>
            <!-- FIXME: v-if="more" creates NameError -->
            <template v-if="props['more']">
              <child name="c" />
              <child name="d" />
            </template>
          </content>
        </template>

        <script lang="python">
        import collagraph as cg

        class Template(cg.Component):
            pass
        </script>
        """
    )

    gui = Collagraph(DictRenderer(), event_loop_type=EventLoopType.SYNC)
    container = {"type": "root"}
    state = reactive({"more": False})

    gui.render(Template, container, state=state)

    content = container["children"][0]
    assert content["type"] == "content"

    assert len(content["children"]) == 2
    for child, name in zip(content["children"], ["a", "b"]):
        assert child["type"] == "child"
        assert child["attrs"]["name"] == name

    state["more"] = True

    assert len(content["children"]) == 4
    for child, name in zip(content["children"], ["a", "b", "c", "d"]):
        assert child["type"] == "child"
        assert child["attrs"]["name"] == name
