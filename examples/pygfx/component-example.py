import pygfx as gfx
from wgpu.gui.auto import WgpuCanvas, run

import collagraph as cg
from examples.pygfx.numberpad import NumberPad

if __name__ == "__main__":
    canvas = WgpuCanvas(size=(600, 400))
    renderer = gfx.renderers.WgpuRenderer(canvas)

    camera = gfx.PerspectiveCamera(60, 16 / 9)
    camera.local.z = 7
    camera.local.y = -2
    camera.show_pos((0, 0, 0))

    controls = gfx.OrbitController(camera)
    controls.register_events(renderer)

    point_light = gfx.PointLight()
    point_light.local.position = [10, 30, 40]
    container = gfx.Scene()
    container.add(gfx.AmbientLight())
    container.add(gfx.DirectionalLight())
    container.add(point_light)

    def animate():
        renderer.render(container, camera)

    gui = cg.Collagraph(renderer=cg.PygfxRenderer())
    gui.renderer.add_on_change_handler(lambda: canvas.request_draw(animate))
    gui.render(NumberPad, container)
    run()
