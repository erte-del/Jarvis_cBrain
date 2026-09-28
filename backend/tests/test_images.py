"""Image editing and storage tests (no network). Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from storage import image_store
from tools.image_ops import EditError, apply_all


def sample(w: int = 400, h: int = 200) -> Image.Image:
    img = Image.new("RGB", (w, h), (200, 60, 40))
    img.paste((20, 120, 220), (0, 0, w // 2, h))  # left half blue
    return img


class OpsTest(unittest.TestCase):
    def run_ops(self, ops, img=None):
        return apply_all(img or sample(), ops)[0]

    def test_crop_fractions_and_aspect(self):
        self.assertEqual(self.run_ops([{"op": "crop", "left": 0, "right": 0.5}]).size, (200, 200))
        self.assertEqual(self.run_ops([{"op": "crop", "aspect": "1:1"}]).size, (200, 200))

    def test_rotate_resize_border(self):
        self.assertEqual(self.run_ops([{"op": "rotate", "degrees": 90}]).size, (200, 400))
        self.assertEqual(self.run_ops([{"op": "resize", "width": 100}]).size, (100, 50))
        self.assertEqual(self.run_ops([{"op": "add_border", "width": 0.05}]).size, (420, 220))

    def test_rotate_is_clockwise(self):
        img = self.run_ops([{"op": "rotate", "degrees": 90}])
        self.assertGreater(img.getpixel((100, 10))[2], 150)  # blue left half is now on top

    def test_colour_ops(self):
        gray = self.run_ops([{"op": "grayscale"}])
        r, g, b = gray.getpixel((10, 10))
        self.assertTrue(r == g == b)
        dark = self.run_ops([{"op": "brightness", "factor": 0.5}])
        self.assertLess(sum(dark.getpixel((10, 10))), sum(sample().getpixel((10, 10))))
        self.run_ops([{"op": "sepia"}, {"op": "blur", "radius": 2}, {"op": "sharpen"}, {"op": "contrast", "factor": 1.2}])

    def test_add_text_changes_pixels(self):
        before = sample()
        after = self.run_ops([{"op": "add_text", "text": "Hello", "position": "center"}], before.copy())
        self.assertNotEqual(before.tobytes(), after.tobytes())

    def test_note(self):
        _, note = apply_all(sample(), [{"op": "crop", "aspect": "1:1"}, {"op": "add_text", "text": "x"}])
        self.assertEqual(note, "crop, add text")

    def test_bad_requests_are_explained(self):
        for ops in [
            [],
            [{"op": "explode"}],
            [{"op": "crop", "left": 0.6, "right": 0.5}],
            [{"op": "brightness", "factor": "lots"}],
            [{"op": "add_text"}],
            [{"op": "add_text", "text": "x", "color": "not-a-colour"}],
            [{"op": "resize", "scale": 50}],
        ]:
            with self.assertRaises(EditError, msg=ops):
                apply_all(sample(), ops)


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = image_store.ASSETS_DIR
        image_store.ASSETS_DIR = Path(self.tmp.name)

    def tearDown(self):
        image_store.ASSETS_DIR = self.old
        self.tmp.cleanup()

    def new_image(self):
        buf = io.BytesIO()
        sample().save(buf, "JPEG")
        return image_store.create("Test", buf.getvalue(), {"photographer": "Ann"})

    def test_versions_and_undo(self):
        rec = self.new_image()
        self.assertEqual((rec.id, rec.current), ("img_001", 1))
        edited, note = apply_all(image_store.open_version(rec), [{"op": "grayscale"}])
        v2 = image_store.add_version(rec, edited, 1, note)
        self.assertEqual((v2.version, v2.parent, rec.current), (2, 1, 2))

        again = image_store.load(rec.id)  # survives a reload from disk
        self.assertEqual([v.version for v in again.versions], [1, 2])
        image_store.set_current(again, 1)
        self.assertEqual(image_store.load(rec.id).current, 1)
        self.assertEqual(self.new_image().id, "img_002")

    def test_card_data(self):
        data = image_store.card_data(self.new_image())
        self.assertEqual(data["versions"][0]["url"], "/assets/img_001/v1.jpg")
        self.assertEqual(data["credit"]["photographer"], "Ann")

    def test_only_image_files_can_be_served(self):
        rec = self.new_image()
        self.assertTrue(image_store.file_path(rec.id, "v1.jpg").exists())
        self.assertTrue(image_store.file_path(rec.id, "v1_thumb.jpg").exists())
        for image_id, name in [
            (rec.id, "meta.json"),
            (rec.id, "../../config.py"),
            ("..", "v1.jpg"),
            ("img_001/..", "v1.jpg"),
            (rec.id, "v9.jpg"),
        ]:
            with self.assertRaises(KeyError, msg=(image_id, name)):
                image_store.file_path(image_id, name)


if __name__ == "__main__":
    unittest.main()
