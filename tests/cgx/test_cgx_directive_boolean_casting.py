from collagraph.cgx import cgx


def test_directive_boolean_casting():
    Labels, _ = cgx.load_from_string(
        """
        <template>
          <widget>
            <label disabled />
          </widget>
        </template>

        <script lang="python">
        import collagraph as cg


        class Labels(cg.Component):
            pass
        </script>
        """
    )

    component = Labels({})
    node = component.render()

    assert node.type == "widget"
    assert len(node.children) == 1

    label = node.children[0]
    assert "disabled" in label.props
    assert label.props["disabled"] is True
