"""AI images, with fake mflux commands instead of FLUX. Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import asyncio
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from storage import image_store
from tools import imagegen, registry

# Stands in for mflux-generate-flux2(-edit): writes a --width × --height PNG to --output
# and records its arguments next to it.
FAKE_MFLUX = f"""#!{sys.executable}
import json, sys
from PIL import Image
a = sys.argv[1:]
get = lambda k: a[a.index(k) + 1]
json.dump(a, open(__file__ + ".args", "w"))
if "FAIL" in get("--prompt"):
    sys.exit(1)
Image.new("RGB", (int(get("--width")), int(get("--height"))), "red").save(get("--output"))
"""


def png(w, h):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), "blue").save(buf, "PNG")
    return buf.getvalue()


class ImageGenTest(unittest.TestCase):
    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        flux = tmp / "flux"
        (flux / ".venv" / "bin").mkdir(parents=True)
        (flux / "flux2-klein-4b-q8").mkdir()
        self.bins = flux / ".venv" / "bin"
        for name in ("mflux-generate-flux2", "mflux-generate-flux2-edit"):
            (self.bins / name).write_text(FAKE_MFLUX)
            (self.bins / name).chmod(0o755)
        for patch in (
            mock.patch.object(image_store, "ASSETS_DIR", tmp / "assets"),
            mock.patch.object(imagegen.config, "FLUX_DIR", flux),
            mock.patch("tools.images.hub.emit", mock.AsyncMock()),
        ):
            patch.start()
            self.addCleanup(patch.stop)

    def args_of(self, name):
        return json.loads((self.bins / f"{name}.args").read_text())

    def test_fit_keeps_shape_under_1024_in_16s(self):
        self.assertEqual(imagegen.fit(1880, 1253), (1024, 688))
        self.assertEqual(imagegen.fit(640, 480), (640, 480))
        w, h = imagegen.fit(1000, 3000)
        self.assertEqual((w % 16, h % 16, max(w, h)), (0, 0, 1024))

    def test_generate_makes_a_new_image(self):
        result = asyncio.run(imagegen.generate_image.handler({"prompt": "a fox", "orientation": "portrait"}))
        self.assertNotIn("is_error", result)
        rec = image_store.load("img_001")
        self.assertEqual((rec.get().width, rec.get().height), (768, 1024))
        self.assertIn("FLUX.2", rec.credit["source"])
        self.assertEqual(result["content"][1]["type"], "image")  # Claude sees it
        self.assertNotIn("--image-paths", self.args_of("mflux-generate-flux2"))

    def test_ai_edit_adds_a_version_from_source_and_references(self):
        src = image_store.create("photo", png(1880, 1253), {})
        ref = image_store.create("glasses", png(400, 400), {})
        result = asyncio.run(imagegen.image_ai_edit.handler(
            {"image_id": src.id, "instruction": "add glasses", "reference_ids": [ref.id]}))
        self.assertNotIn("is_error", result)
        rec = image_store.load(src.id)
        self.assertEqual((rec.current, rec.get().parent, rec.get().note), (2, 1, "AI: add glasses"))
        args = self.args_of("mflux-generate-flux2-edit")
        paths = args[args.index("--image-paths") + 1:]
        self.assertTrue(paths[0].endswith(f"{src.id}/v1.jpg") and paths[1].endswith(f"{ref.id}/v1.jpg"))
        self.assertEqual(args[args.index("--width") + 1], "1024")

    def test_failures_are_reported(self):
        failed = asyncio.run(imagegen.generate_image.handler({"prompt": "FAIL"}))
        self.assertIn("failed", failed["content"][0]["text"])
        missing = asyncio.run(imagegen.image_ai_edit.handler({"image_id": "img_999", "instruction": "x"}))
        self.assertTrue(missing["is_error"])
        with mock.patch.object(imagegen.config, "FLUX_DIR", Path("/nonexistent")):
            not_set_up = asyncio.run(imagegen.generate_image.handler({"prompt": "a fox"}))
        self.assertIn("setup_images.sh", not_set_up["content"][0]["text"])

    def test_tools_run_without_asking(self):
        for name in ("generate_image", "image_ai_edit"):
            self.assertEqual(registry.classify(f"mcp__jarvis__{name}"), "read")


if __name__ == "__main__":
    unittest.main()
