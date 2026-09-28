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


if __name__ == "__main__":
    unittest.main()
