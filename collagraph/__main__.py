from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

from observ import reactive

import collagraph as cg


def available_renderers():
    result = set()
    for renderer_type, name in {
        "PySideRenderer": "pyside",
        "PygfxRenderer": "pygfx",
        "DictRenderer": "dict",
        # TODO: add support for DomRenderer
        # "DomRenderer": "dom",
    }.items():
        try:
            importlib.import_module("collagraph", renderer_type)
            result.add(name)
        except ImportError:
            continue
    return result


def init_collagraph(
    renderer_type: str, component_path: Path, state: dict | None = None
):
    component_class, _ = cg.sfc.compiler.load(component_path)
    props = reactive(state or {})

    if renderer_type == "pygfx":
        import pygfx as gfx
        from wgpu.gui.auto import WgpuCanvas, run

        canvas = WgpuCanvas(size=(600, 400))
        wgpu_renderer = gfx.renderers.WgpuRenderer(canvas)

        camera = gfx.PerspectiveCamera(70, 16 / 9)
        camera.local.z = 15
        camera.show_pos((0, 0, 0))

        controls = gfx.OrbitController(camera)
        controls.register_events(wgpu_renderer)

        container = gfx.Scene()

        def animate():
            wgpu_renderer.render(container, camera)

        renderer = cg.PygfxRenderer()
        renderer.add_on_change_handler(lambda: canvas.request_draw(animate))
        gui = cg.Collagraph(renderer=renderer)
        gui.render(component_class, container, state=props)

        run()
    elif renderer_type == "pyside":
        from PySide6 import QtWidgets

        app = QtWidgets.QApplication()
        gui = cg.Collagraph(renderer=cg.PySideRenderer())
        gui.render(component_class, app, state=props)
        app.exec()
    elif renderer_type == "dict":
        container = {"root": None}
        gui = cg.Collagraph(
            renderer=cg.DictRenderer(),
            event_loop_type=cg.EventLoopType.SYNC,
        )
        gui.render(component_class, container, state=props)
        # Start debugger to allow for inspection of container
        # and manipulation of props
        breakpoint()  # noqa: T100


def existing_component_file(value):
    path = Path(value)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"{value} does not exist")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"{value} is not a file")
    if path.suffix != ".cgx":
        raise argparse.ArgumentTypeError(f"{value} is not a collagraph component")
    return path


def json_contents(value):
    path = Path(value)
    if path.is_file():
        with path.open(mode="r", encoding="utf-8") as fh:
            try:
                return json.load(fh)
            except Exception:
                raise argparse.ArgumentTypeError(f"{value} is not valid json")
    else:
        try:
            return json.loads(value)
        except Exception:
            raise argparse.ArgumentTypeError(f"{value} is not valid json")


def run():
    parser = argparse.ArgumentParser(
        description="Run collagraph components directly",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--renderer",
        default="pyside",
        choices=available_renderers(),
        help="The type of renderer to use",
    )
    parser.add_argument(
        "--state",
        type=json_contents,
        help="Optional state/props to load (json file or string)",
    )
    parser.add_argument(
        "component",
        type=existing_component_file,
        help="Path to component to render",
    )
    args = parser.parse_args()

    init_collagraph(args.renderer, args.component, args.state)


if __name__ == "__main__":
    run()
