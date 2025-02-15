import pytest

from collagraph import Collagraph, EventLoopType
from collagraph.renderers import DictRenderer


def test_parser_unclosed_element(parse_source):
    App, _ = parse_source(
        """
        <app>
          <unclosed>
        </app>

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

    assert container["children"][0] == {
        "type": "app",
        "children": [
            {"type": "unclosed"},
        ],
    }


def test_parser_unclosed_root_element(parse_source):
    with pytest.raises(ValueError):
        _ = parse_source(
            """
            <app>

            <script>
            import collagraph as cg

            class App(cg.Component):
                pass
            </script>
            """
        )
