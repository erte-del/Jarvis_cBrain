"""Runs INSIDE Blender (never imported by Jarvis). Fixed script: Claude never writes code that runs here.

    Blender --background --factory-startup --python blender_export_script.py -- <in.glb> <out> <format>

Imports the detailed model Jarvis built, smooths round surfaces, adds small
bevels to boxes and extruded shapes, and saves it in the requested format.
"""

import math
import sys

import bpy

src, dst, fmt = sys.argv[sys.argv.index("--") + 1 :][:3]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for obj in meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
# Smooth curved surfaces but keep sharp edges sharp.
bpy.ops.object.shade_auto_smooth(angle=math.radians(35))

for obj in meshes:
    # Node names look like "003_seat__box" (set by tools/shapes.py).
    if obj.name.split(".")[0].endswith(("__box", "__extrude")):
        smallest = min(d for d in obj.dimensions if d > 0)
        bevel = obj.modifiers.new("Bevel", "BEVEL")
        bevel.width = smallest * 0.04
        bevel.segments = 3
        bevel.limit_method = "ANGLE"

if fmt == "blend":
    bpy.ops.wm.save_as_mainfile(filepath=dst, compress=True)
elif fmt == "fbx":
    bpy.ops.export_scene.fbx(filepath=dst, use_mesh_modifiers=True, path_mode="COPY", embed_textures=True)
elif fmt == "obj":
    bpy.ops.wm.obj_export(filepath=dst, apply_modifiers=True, export_materials=True)
elif fmt == "stl":
    # 3D printers and slicers expect millimeters.
    bpy.ops.wm.stl_export(filepath=dst, apply_modifiers=True, global_scale=1000.0)
elif fmt == "glb":
    bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_apply=True)
elif fmt == "gltf":
    bpy.ops.export_scene.gltf(filepath=dst, export_format="GLTF_SEPARATE", export_apply=True)
else:
    raise SystemExit(f"unknown format {fmt}")

print(f"JARVIS_EXPORT_OK {dst}")
