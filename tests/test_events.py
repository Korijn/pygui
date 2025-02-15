import pytest

from collagraph import Collagraph, EventLoopType
from collagraph.renderers import DictRenderer


def test_reactive_element_with_events(parse_source):
    """
    Events can either be method names, or they have to be
    lambdas or functions that can be called.
    """
    App, _ = parse_source(
        """
        <count
          :count="count"
          @bump="bump"
          @skip="lambda: skip(3)"
        />

        <script>
        import collagraph as cg

        class App(cg.Component):
            def __init__(self, props):
                super().__init__(props)
                self.state["count"] = 0

            def bump(self):
                self.state["count"] += 1

            def skip(self, amount):
                self.state["count"] += amount
        </script>
        """
    )

    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )

    gui.render(App, container)

    count = container["children"][0]
    assert count["type"] == "count"
    assert count["attrs"]["count"] == 0
    assert len(count["handlers"]["bump"]) == 1

    # Update state by triggering all listeners, which should trigger a re-render
    for handler in count["handlers"]["bump"]:
        handler()

    assert count["attrs"]["count"] == 1

    for handler in count["handlers"]["skip"]:
        handler()

    assert count["attrs"]["count"] == 4


def test_events_outside_component(parse_source):
    Example, _ = parse_source(
        """
        <button @clicked="clicked" />
        <button @clicked="lambda ev: callback(ev, 'two')" />
        <button @clicked="lambda ev: class_callback(ev, 'three')" />

        <script>
        from collagraph import Component

        def callback(ev, name):
            Example.callbacks.append((ev, name))

        class Example(Component):
            callbacks = []

            def clicked(self):
                Example.callbacks.append(('clicked', 'one'))

            def class_callback(self, ev, name):
                Example.callbacks.append((ev, name))
        </script>
        """
    )

    container = {"type": "root"}
    gui = Collagraph(
        renderer=DictRenderer(),
        event_loop_type=EventLoopType.SYNC,
    )

    gui.render(Example, container)

    button_one, button_two, button_three = container["children"]

    for handler in button_one["handlers"]["clicked"]:
        handler()

    assert len(Example.callbacks) == 1
    assert Example.callbacks[-1] == ("clicked", "one")

    for handler in button_two["handlers"]["clicked"]:
        handler("clicked")

    assert len(Example.callbacks) == 2
    assert Example.callbacks[-1] == ("clicked", "two")

    for handler in button_three["handlers"]["clicked"]:
        handler("clicked")

    assert len(Example.callbacks) == 3
    assert Example.callbacks[-1] == ("clicked", "three")


def test_unsupported_syntax(parse_source):
    """
    Show unsupported syntax for events.
    """
    with pytest.raises(SyntaxError):
        parse_source(
            """
            <node @bump="count += 1" />

            <script>
            import collagraph as cg

            class Counter(cg.Component):
                pass
            </script>
            """
        )

    with pytest.raises(SyntaxError):
        parse_source(
            """
            <node @reset="count = 0" />

            <script>
            import collagraph as cg

            class Counter(cg.Component):
                pass
            </script>
            """
        )
