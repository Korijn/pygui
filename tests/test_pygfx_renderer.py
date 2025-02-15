import math
from collections import namedtuple

import pytest

try:
    import pygfx as gfx
except ImportError:
    pytest.skip(reason="pygfx not installed", allow_module_level=True)

from collagraph.renderers import PygfxRenderer


def test_pygfx_create_element():
    renderer = PygfxRenderer()

    obj = renderer.create_element("Scene")
    assert isinstance(obj, gfx.Scene)

    obj = renderer.create_element("scene")
    assert isinstance(obj, gfx.Scene)

    obj = renderer.create_element("Mesh")
    assert isinstance(obj, gfx.Mesh)

    obj = renderer.create_element("MeshBasicMaterial")
    assert isinstance(obj, gfx.MeshBasicMaterial)

    with pytest.raises(ValueError):
        renderer.create_element("Foo")


def test_pygfx_text_element_not_supported():
    renderer = PygfxRenderer()
    obj = renderer.create_element("scene")

    with pytest.raises(NotImplementedError):
        renderer.create_text_element()

    with pytest.raises(NotImplementedError):
        renderer.set_element_text(obj, "Foo")


def test_pygfx_insert_remove():
    renderer = PygfxRenderer()

    parent = gfx.Scene()

    child1 = gfx.WorldObject()
    child2 = gfx.WorldObject()

    def equals(a, b):
        if len(a) != len(b):
            return False
        for x, y in zip(a, b):
            if x != y:
                return False
        return True

    renderer.insert(child1, parent)
    assert equals(parent.children, (child1,))

    renderer.insert(child2, parent)
    assert equals(parent.children, (child1, child2))

    renderer.insert(child2, parent, anchor=child1)
    assert equals(parent.children, (child2, child1))

    renderer.remove(child2, parent)
    assert equals(parent.children, (child1,))

    renderer.remove(child1, parent)
    assert equals(parent.children, ())


def test_pygfx_attributes():
    renderer = PygfxRenderer()

    # Set and unset attributes on Mesh
    mesh = gfx.Mesh()

    # Custom attribute 'name'
    renderer.set_attribute(mesh, "name", "foo")
    assert mesh.name == "foo"

    renderer.remove_attribute(mesh, "name", "foo")
    assert not hasattr(mesh, "name")

    # Position attribute
    original_position_contents = mesh.local.position.tolist()
    renderer.set_attribute(mesh, "local.position", (3, 2, 5))

    assert mesh.local.position.tolist() == [3, 2, 5]

    renderer.remove_attribute(mesh, "local.position", [3, 2, 5])
    assert mesh.local.position.tolist() == original_position_contents

    # Rotation attribute
    original_rotation_contents = mesh.local.rotation.tolist()
    renderer.set_attribute(mesh, "local.rotation", [0, 1, 0, 0])
    assert mesh.local.rotation.tolist() == [0, 1, 0, 0]

    renderer.remove_attribute(mesh, "local.rotation", [1, 2, 3, 4])
    assert mesh.local.rotation.tolist() == original_rotation_contents

    # Matrix attribute
    original_matrix_contents = mesh.local.matrix.tolist()
    matrix = [[2, 0, 0, 0], [0, 2, 0, 0], [0, 0, 2, 0], [0, 0, 0, 2]]
    renderer.set_attribute(mesh, "local.matrix", matrix)
    assert mesh.local.matrix.tolist() == matrix

    renderer.remove_attribute(mesh, "local.matrix", [1] * 16)
    assert mesh.local.matrix.tolist() == original_matrix_contents

    # Set and unset attributes on Material
    material = gfx.LineMaterial()

    # Color attribute
    original_color_hex = material.color.hex
    renderer.set_attribute(material, "color", [1, 0.5, 0, 0.8])
    assert material.color.hex == gfx.Color(1, 0.5, 0, 0.8).hex

    renderer.remove_attribute(material, "color", [1, 0.5, 0, 0.8])
    assert material.color.hex == original_color_hex

    # Opacity attribute
    original_opacity = material.opacity
    renderer.set_attribute(material, "opacity", 0.5)
    assert math.isclose(material.opacity, 0.5)

    renderer.remove_attribute(material, "opacity", 0.5)
    assert material.opacity == original_opacity

    # Clipping planes attribute
    original_clipping_planes = material.clipping_planes.copy()
    renderer.set_attribute(material, "clipping_planes", [(0, 1, 2, 3)])
    assert material.clipping_planes[0] == (0, 1, 2, 3)

    renderer.remove_attribute(material, "clipping_planes", [(0, 1, 2, 3)])
    assert material.clipping_planes == original_clipping_planes


def test_event_handlers():
    renderer = PygfxRenderer()

    count = 0

    def counter(event):
        nonlocal count
        count += 1

    obj = gfx.Scene()
    renderer.add_event_listener(obj, "click", counter)

    Event = namedtuple("Event", ["type", "cancelled"], defaults=[False])
    event = Event("click")
    obj.handle_event(event)

    assert count == 1

    renderer.remove_event_listener(obj, "click", counter)

    obj.handle_event(event)

    assert count == 1
