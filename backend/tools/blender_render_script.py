"""Runs INSIDE Blender (never imported by Jarvis). Fixed script: Claude never writes code that runs here.

    Blender --background --factory-startup --python blender_render_script.py -- <in.glb> <out_dir>

Renders four quick views of a 3D preview (3/4, side, front, top) so Claude can
check its own work. Writes three_quarter.png, side.png, front.png, top.png.
"""

import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector

src, out_dir = sys.argv[sys.argv.index("--") + 1 :][:2]
SIZE = 384

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == "MESH"]
corners = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(c[i] for c in corners) for i in range(3)])
hi = Vector([max(c[i] for c in corners) for i in range(3)])
center, radius = (lo + hi) / 2, max((hi - lo).length / 2, 0.01)

# Fast, clear "clay" look with outlines so separate parts are easy to tell apart.
scene.render.engine = "BLENDER_WORKBENCH"
shading = scene.display.shading
shading.light = "STUDIO"
shading.color_type = "MATERIAL"
shading.show_cavity = True
shading.show_object_outline = True
shading.object_outline_color = (0.05, 0.05, 0.05)
scene.world = bpy.data.worlds.new("bg")
scene.world.color = (0.55, 0.58, 0.62)
scene.render.resolution_x = scene.render.resolution_y = SIZE
scene.render.image_settings.file_format = "PNG"

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = radius * 2.15
cam.data.clip_start = radius * 0.01
cam.data.clip_end = radius * 20

# After glTF import Blender is Z-up: our +X (front) stays +X, our +Z (left/right) is Blender -Y.
views = {
    "three_quarter": Vector((1.0, -1.0, 0.7)),
    "side": Vector((0.0, -1.0, 0.0)),
    "front": Vector((1.0, 0.0, 0.0)),
    "top": None,  # straight down
}
for name, direction in views.items():
    if direction is None:
        cam.location = center + Vector((0, 0, radius * 4))
        cam.rotation_euler = Euler((0, 0, 0))
    else:
        direction = direction.normalized()
        cam.location = center + direction * radius * 4
        cam.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(Path(out_dir) / f"{name}.png")
    bpy.ops.render.render(write_still=True)

print("JARVIS_RENDER_OK")
