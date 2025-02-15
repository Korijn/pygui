import pytest

import collagraph as cg


def test_sfc_import():
    from tests.data.simple import Simple

    assert issubclass(Simple, cg.Component)

    gui = cg.Collagraph(
        renderer=cg.DictRenderer(),
        event_loop_type=cg.EventLoopType.SYNC,
    )
    target = {"type": "root"}

    gui.render(Simple, target)

    assert target["children"][0] == {"type": "label", "attrs": {"text": "Simple"}}


def test_sfc_multiple_classes():
    with pytest.raises(ValueError):
        import tests.data.multiple_classes_wrong_order

    import tests.data.multiple_classes_right_order  # noqa: F401


def test_sfc_no_component_class():
    with pytest.raises(ValueError):
        import tests.data.no_component_class  # noqa: F401


def test_cgx_use_imported_component(parse_source):
    Content, namespace = parse_source(
        """
        <content-example :text="content" />

        <script lang="python">
        import collagraph as cg

        class Content(cg.Component):
            pass
        </script>
        """
    )
    Container, namespace = parse_source(
        """
        <Content content="content" />

        <script lang="python">
        import collagraph as cg
        try:
            import Content
        except ImportError:
            pass

        class Container(cg.Component):
            pass
        </script>
        """,
        namespace=namespace,
    )

    container = {"type": "root"}
    gui = cg.Collagraph(cg.DictRenderer(), event_loop_type=cg.EventLoopType.SYNC)
    gui.render(Container, container)

    content = container["children"][0]
    # The container does not actually provide any dom element
    # so the first child should actually be the type that
    # is defined in the Content component.
    assert content["type"] == "content-example"


def test_cgx_use_imported_component_advanced(parse_source):
    ImportVariations, _ = parse_source(
        """
        <list>
          <!-- Functional or class component should start with upper case ... -->
          <Example_component />
          <EC />
          <CE />
          <FooBar />
          <!-- ... or have a dot in their tag
               (which indicates a function/class from a module)
            -->
          <example.Example />
          <tests.data.example.Example />
        </list>

        <script lang="python">
        import collagraph as cg
        from tests.data.example import Example as Example_component
        from tests.data.example import Example as EC
        from tests.data import example
        import tests

        CE = EC
        FooBar = example.Example

        print("Here, we're still good!")

        class ImportVariations(cg.Component):
            pass
        </script>
        """
    )
    # from tests.data.imports import ImportVariations

    container = {"type": "root"}
    gui = cg.Collagraph(cg.DictRenderer(), event_loop_type=cg.EventLoopType.SYNC)
    gui.render(ImportVariations, container)

    content = container["children"][0]
    assert len(content["children"]) == 6
    for idx, child in enumerate(content["children"]):
        assert child["type"] == "example-component", f"Child at {idx}: {child}"
