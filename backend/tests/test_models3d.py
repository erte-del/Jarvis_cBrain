"""3D preview and export tests. Run from the backend folder:
    .venv/bin/python -m unittest discover tests

The export tests run the real Blender in the background (a few seconds each)
and are skipped if Blender isn't installed.
"""

import asyncio
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

import trimesh

import config
from storage import model_store
from tools import models3d, shapes

CHAIR = {"parts": [
    {"name": "seat", "shape": "box", "size": [0.45, 0.05, 0.45], "position": [0, 0.45, 0], "color": "saddlebrown"},
    {"name": "back", "shape": "box", "size": [0.45, 0.45, 0.04], "position": [0, 0.7, -0.2], "color": "saddlebrown"},
    *[{"name": f"leg{i}", "shape": "cylinder", "radius": 0.02, "height": 0.45,
       "position": [x, 0.225, z], "material": "metal", "color": "#888"}
      for i, (x, z) in enumerate([(0.2, 0.2), (-0.2, 0.2), (0.2, -0.2), (-0.2, -0.2)], 1)],
]}


CAR = {"parts": [
    {"name": "body", "shape": "loft", "color": "gold", "sections": [
        {"x": -2.2, "y": 0.55, "width": 1.6, "height": 0.5, "roundness": 0.4, "bottom_roundness": 0.1},
        {"x": 0.0, "y": 0.62, "width": 1.8, "height": 0.7, "roundness": 0.5, "bottom_roundness": 0.1},
        {"x": 2.2, "y": 0.45, "width": 1.5, "height": 0.25, "roundness": 0.8}]},
    {"name": "wheel_front", "shape": "cylinder", "radius": 0.34, "height": 0.26, "rotation": [90, 0, 0],
     "position": [1.4, 0.34, 0.8], "color": "#222", "mirror": True},
    {"name": "wheel_rear", "shape": "cylinder", "radius": 0.34, "height": 0.26, "rotation": [90, 0, 0],
     "position": [-1.4, 0.34, 0.8], "color": "#222", "mirror": True},
]}


class NewShapesTest(unittest.TestCase):
    def test_loft_is_smooth_solid_and_follows_sections(self):
        scene = shapes.build_scene(shapes.validate(CAR), "final")
        body = scene.geometry["001_body"]
        self.assertTrue(body.is_watertight)
        self.assertGreater(body.volume, 0)
        self.assertAlmostEqual(body.extents[0], 4.4, places=2)  # length along X
        self.assertAlmostEqual(body.extents[2], 1.8, places=1)  # widest section, along Z

    def test_mirror_adds_the_other_side(self):
        scene = shapes.build_scene(shapes.validate(CAR))
        self.assertEqual(len(scene.geometry), 5)  # body + 2 wheels × 2
        left, right = scene.geometry["002_wheel_front"], scene.geometry["002m_wheel_front (mirrored)"]
        self.assertAlmostEqual(left.centroid[2], -right.centroid[2], places=3)
        self.assertGreater(right.volume, 0)  # still faces outward after reflecting

    def test_rounded_box_keeps_its_size(self):
        spec = {"parts": [{"shape": "box", "size": [1, 0.5, 0.8], "round": 0.3}]}
        mesh = next(iter(shapes.build_scene(shapes.validate(spec)).geometry.values()))
        self.assertTrue(all(abs(a - b) < 0.01 for a, b in zip(mesh.extents, [1, 0.5, 0.8])))
        self.assertLess(mesh.volume, 1 * 0.5 * 0.8)  # corners are cut off

    def test_bad_new_fields_are_explained(self):
        for part in [
            {"shape": "loft", "sections": [{"x": 0, "width": 1, "height": 1}]},  # one section
            {"shape": "loft", "sections": [{"x": 1, "width": 1, "height": 1}, {"x": 0, "width": 1, "height": 1}]},
            {"shape": "loft", "sections": [{"x": 0, "width": 1}, {"x": 1, "width": 1, "height": 1}]},
            {"shape": "loft", "sections": [{"x": 0, "width": 1, "height": 1, "roundness": 2},
                                           {"x": 1, "width": 1, "height": 1}]},
            {"shape": "box", "size": [1, 1, 1], "round": 0.9},
            {"shape": "box", "size": [1, 1, 1], "mirror": "sideways"},
        ]:
            with self.assertRaises(shapes.SpecError, msg=part):
                shapes.validate({"parts": [part]})


class SmallChangesTest(unittest.TestCase):
    def test_update_add_remove(self):
        new = shapes.apply_changes(
            CHAIR,
            update_parts=[{"name": "seat", "color": "red", "position": [0, 0.5, 0]}],
            add_parts=[{"name": "cushion", "shape": "box", "size": [0.4, 0.05, 0.4], "position": [0, 0.5, 0]}],
            remove_parts=["leg4"],
        )
        names = [p["name"] for p in new["parts"]]
        self.assertEqual(names, ["seat", "back", "leg1", "leg2", "leg3", "cushion"])
        self.assertEqual(new["parts"][0]["color"], "red")
        self.assertEqual(CHAIR["parts"][0]["color"], "saddlebrown")  # the original isn't touched
        shapes.validate(new)

    def test_null_removes_a_field(self):
        spec = {"parts": [{"name": "b", "shape": "box", "size": [1, 1, 1], "round": 0.2}]}
        self.assertNotIn("round", shapes.apply_changes(spec, update_parts=[{"name": "b", "round": None}])["parts"][0])

    def test_unknown_names_list_the_real_ones(self):
        with self.assertRaises(shapes.SpecError) as err:
            shapes.apply_changes(CHAIR, remove_parts=["legs"])
        self.assertIn("'leg1'", str(err.exception))


class FloatingTest(unittest.TestCase):
    def floating(self, spec):
        return shapes.floating_parts(shapes.build_scene(shapes.validate(spec)))

    def test_connected_objects_pass(self):
        self.assertEqual(self.floating(CHAIR), [])
        self.assertEqual(self.floating(CAR), [])

    def test_a_floating_part_is_reported_with_its_gap(self):
        spec = {"parts": [*CHAIR["parts"],
                          {"name": "lamp", "shape": "sphere", "radius": 0.05, "position": [0, 1.2, 0]}]}
        result = self.floating(spec)
        self.assertEqual([name for name, _ in result], ["lamp"])
        # Nearest chair point is the top edge of the backrest at (0, 0.925, -0.18):
        # distance from the lamp's center (0, 1.2, 0) minus its radius.
        self.assertAlmostEqual(result[0][1], (0.275**2 + 0.18**2) ** 0.5 - 0.05, delta=0.01)

    def test_a_part_inside_another_counts_as_attached(self):
        spec = {"parts": [{"name": "block", "shape": "box", "size": [1, 1, 1]},
                          {"name": "core", "shape": "sphere", "radius": 0.1}]}
        self.assertEqual(self.floating(spec), [])


class ShapesTest(unittest.TestCase):
    def test_every_shape_builds(self):
        spec = {"parts": [
            {"shape": "box", "size": [1, 1, 1]},
            {"shape": "sphere", "radius": 0.5, "scale": [1, 2, 1]},
            {"shape": "cylinder", "radius_top": 0.1, "radius_bottom": 0.3, "height": 1},
            {"shape": "cone", "radius": 0.3, "height": 1},
            {"shape": "torus", "radius": 0.5, "tube": 0.1},
            {"shape": "capsule", "radius": 0.1, "height": 1},
            {"shape": "lathe", "points": [[0, 0], [0.3, 0], [0.2, 0.5], [0.25, 0.8]]},
            {"shape": "extrude", "outline": [[0, 0], [1, 0], [0.5, 1]], "depth": 0.1},
        ]}
        scene = shapes.build_scene(shapes.validate(spec))
        self.assertEqual(len(scene.geometry), 8)

    def test_sizes_and_y_up(self):
        size, _ = shapes.summary(shapes.build_scene(shapes.validate(CHAIR)))
        self.assertEqual(size, [0.45, 0.925, 0.45])  # height is Y
        cyl = shapes.build_scene(shapes.validate({"parts": [{"shape": "cylinder", "radius": 0.1, "height": 2}]}))
        self.assertAlmostEqual(shapes.summary(cyl)[0][1], 2.0, places=2)  # upright

    def test_final_has_more_detail_than_preview(self):
        parts = shapes.validate(CHAIR)
        _, low = shapes.summary(shapes.build_scene(parts, "preview"))
        _, high = shapes.summary(shapes.build_scene(parts, "final"))
        self.assertGreater(high, low * 3)

    def test_glb_round_trip(self):
        glb = shapes.to_glb(shapes.build_scene(shapes.validate(CHAIR)))
        self.assertEqual(len(trimesh.load(io.BytesIO(glb), file_type="glb").geometry), 6)

    def test_bad_specs_are_explained(self):
        for spec in [None, {"parts": "x"}, {"parts": [{"shape": "cube"}]},
                     {"parts": [{"shape": "sphere", "radius": -1}]},
                     {"parts": [{"shape": "box", "size": [1, 1, 1], "material": "wood"}]},
                     {"parts": [{"shape": "box", "size": [1, 1, 1], "position": [0, 0]}]},
                     {"parts": [{"shape": "lathe", "points": [[-1, 0], [1, 1]]}]}]:
            with self.assertRaises(shapes.SpecError, msg=spec):
                shapes.validate(spec)


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = model_store.MODELS_DIR
        model_store.MODELS_DIR = Path(self.tmp.name)

    def tearDown(self):
        model_store.MODELS_DIR = self.old
        self.tmp.cleanup()

    def preview(self, **args):
        return asyncio.run(models3d.preview_3d.handler({"spec": CHAIR, **args}))

    def test_preview_versions_and_revert(self):
        self.assertIn("mdl_001 v1", self.preview(title="Chair")["content"][0]["text"])
        self.assertIn("mdl_001 v2", self.preview(model_id="mdl_001", note="taller")["content"][0]["text"])
        rec = model_store.load("mdl_001")
        self.assertEqual((rec.title, rec.current, len(rec.versions)), ("Chair", 2, 2))
        asyncio.run(models3d.revert_3d.handler({"model_id": "mdl_001"}))
        self.assertEqual(model_store.load("mdl_001").current, 1)
        self.assertEqual(model_store.spec(rec, 1), CHAIR)

    def test_small_change_makes_a_new_version(self):
        self.preview(title="Chair")
        result = asyncio.run(models3d.preview_3d.handler(
            {"model_id": "mdl_001", "update_parts": [{"name": "seat", "color": "red"}], "note": "red seat"}))
        self.assertFalse(result.get("is_error"), result)
        rec = model_store.load("mdl_001")
        self.assertEqual(rec.current, 2)
        self.assertEqual(model_store.spec(rec, 2)["parts"][0]["color"], "red")
        self.assertEqual(model_store.spec(rec, 1)["parts"][0]["color"], "saddlebrown")

    def test_needs_a_spec_or_a_change(self):
        result = asyncio.run(models3d.preview_3d.handler({"title": "Nothing"}))
        self.assertTrue(result.get("is_error"))

    def test_bad_spec_makes_no_version(self):
        result = asyncio.run(models3d.preview_3d.handler({"spec": {"parts": []}}))
        self.assertTrue(result.get("is_error"))
        self.assertEqual(list(Path(self.tmp.name).iterdir()), [])

    def test_only_model_files_can_be_served(self):
        self.preview(title="Chair")
        self.assertTrue(model_store.file_path("mdl_001", "v1_preview.glb").exists())
        for model_id, name in [("mdl_001", "meta.json"), ("mdl_001", "v1.json"),
                               ("mdl_001", "../../config.py"), ("..", "v1_preview.glb"),
                               ("mdl_001", "final_v1.exe")]:
            with self.assertRaises(KeyError, msg=(model_id, name)):
                model_store.file_path(model_id, name)

    @unittest.skipUnless(Path(config.BLENDER_PATH).exists(), "Blender not installed")
    def test_export_every_format_with_blender(self):
        self.preview(title="Test Chair")
        rec = model_store.load("mdl_001")
        expected = {"blend": ".blend", "fbx": ".fbx", "stl": ".stl", "glb": ".glb", "obj": ".zip", "gltf": ".zip"}
        for fmt, ext in expected.items():
            with self.subTest(fmt=fmt):
                name = asyncio.run(models3d.build_final(rec, 1, fmt))
                path = model_store.file_path("mdl_001", name)
                self.assertTrue(name.endswith(ext), name)
                self.assertGreater(path.stat().st_size, 1000)
                if ext == ".zip":
                    inside = zipfile.ZipFile(path).namelist()
                    self.assertTrue(any(n.endswith("." + fmt) for n in inside), inside)
        self.assertEqual(model_store.download_name(rec, "final_v1.fbx"), "test_chair_v1.fbx")
        # The STL is in millimeters: the chair is ~925 mm tall.
        stl = trimesh.load(model_store.file_path("mdl_001", "final_v1.stl"))
        self.assertAlmostEqual(max(stl.extents), 925, delta=15)

    @unittest.skipUnless(Path(config.BLENDER_PATH).exists(), "Blender not installed")
    def test_preview_gives_claude_four_views_and_floating_warning(self):
        spec = {"parts": [*CAR["parts"],
                          {"name": "mirror", "shape": "box", "size": [0.1, 0.08, 0.1],
                           "position": [0.5, 1.1, 1.1], "mirror": True}]}
        result = asyncio.run(models3d.preview_3d.handler({"spec": spec, "title": "Car"}))
        text, image = result["content"][0]["text"], result["content"][1]
        self.assertIn("PROBLEM", text)
        self.assertIn("mirror (", text)
        self.assertEqual(image["type"], "image")
        from PIL import Image
        sheet = Image.open(io.BytesIO(__import__("base64").b64decode(image["data"])))
        self.assertEqual(sheet.size, (768, 768))  # 2 × 2 views

    @unittest.skipUnless(Path(config.BLENDER_PATH).exists(), "Blender not installed")
    def test_loft_and_mirror_export(self):
        asyncio.run(models3d.preview_3d.handler({"spec": CAR, "title": "Car"}))
        rec = model_store.load("mdl_001")
        name = asyncio.run(models3d.build_final(rec, 1, "glb"))
        exported = trimesh.load(model_store.file_path("mdl_001", name))
        self.assertEqual(len(exported.geometry), 5)


if __name__ == "__main__":
    unittest.main()
