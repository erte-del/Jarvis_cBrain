"""Slides: builds a deck from the teacher's template into a temp folder; nothing is opened.
    .venv/bin/python -m unittest tests.test_slides
"""

import asyncio
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image
from pptx import Presentation

from storage import image_store
from tools import registry, slides

DECK = {
    "title": "Logic gates", "unit": "Fundamentals of computer systems", "topic": "2",
    "slides": [
        {"kind": "objectives", "points": ["Knowledge:", "- Know the AND, OR and NOT gates"]},
        {"title": "AND gate", "points": ["Both inputs must be 1"], "table": [["A", "B", "Q"], ["0", "0", "0"], ["1", "1", "1"]],
         "notes": "What happens with 1 and 0?"},
        {"kind": "practice", "title": "Practice", "points": ["1. What is 1 AND 0?"], "notes": "1. 0"},
    ],
}


@unittest.skipUnless(slides.TEMPLATE.exists(), "no slide template in storage")
class SlidesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for patch in (mock.patch.object(slides.config, "FILES_DIR", Path(tmp.name)),
                      mock.patch.object(slides, "CHECKS", Path(tmp.name) / "checks"),
                      mock.patch.object(slides.subprocess, "run")):
            patch.start()
            self.addCleanup(patch.stop)
        self.out = Path(tmp.name) / "Output"

    def make(self):
        return asyncio.run(slides.make_slides.handler(DECK))["content"][0]["text"]

    def test_runs_freely(self):
        self.assertEqual(registry.classify("mcp__jarvis__make_slides"), "read")

    def test_builds_the_deck(self):
        self.assertIn("(5 slides)", self.make())
        deck = Presentation(str(self.out / "Logic gates.pptx"))
        names = [s.slide_layout.name for s in deck.slides]
        self.assertEqual(names, ["Title Slide", "7_Custom Layout", "3_Custom Layout", "2_Custom Layout", "8_Custom Layout"])
        self.assertIn("Logic gates", deck.slides[0].placeholders[11].text_frame.text)
        gate = deck.slides[2]
        self.assertEqual(gate.placeholders[13].text_frame.text, "AND gate")
        self.assertEqual([sh.table.cell(2, 2).text for sh in gate.shapes if sh.has_table], ["1"])
        self.assertEqual(gate.notes_slide.notes_text_frame.text, "What happens with 1 and 0?")
        footer = [sh.text_frame.text for sh in gate.slide_layout.shapes if sh.name.startswith("TextBox")]
        self.assertEqual(footer, ["Fundamentals of computer systems\nTopic 2 Logic gates"])

    def test_never_overwrites(self):
        self.make()
        self.make()
        self.assertTrue((self.out / "Logic gates 2.pptx").exists())

    def test_checked_before_it_is_opened(self):
        path = self.out / "Logic gates.pptx"
        pictures = []
        for n in range(1, 11):
            pictures.append(self.out.parent / f"{n}.jpeg")
            Image.new("RGB", (400, 300), "white").save(pictures[-1])
        with mock.patch.object(slides, "render", return_value=pictures) as render:
            content = asyncio.run(slides.make_slides.handler(DECK))["content"]
            again = asyncio.run(slides.make_slides.handler({**DECK, "replace": str(path)}))["content"]
        self.assertEqual(render.call_args.args, (path, self.out.parent / "checks" / "Logic gates"))
        self.assertEqual([c["type"] for c in content], ["text", "image", "image"])  # 10 slides: 9 + 1
        self.assertIn("Not opened yet", content[0]["text"])
        self.assertIn(str(path), again[0]["text"])
        self.assertFalse((self.out / "Logic gates 2.pptx").exists())
        slides.subprocess.run.assert_not_called()
        self.assertEqual(asyncio.run(slides.open_slides.handler({"file": str(path)}))["content"][0]["text"],
                         f"Opened {path}.")
        slides.subprocess.run.assert_called_once_with(["open", str(path)], check=False)
        self.assertTrue(asyncio.run(slides.open_slides.handler({"file": "/etc/hosts"})).get("is_error"))

    def test_pictures_and_the_teachers_figures(self):
        self.make()
        png = io.BytesIO()
        Image.new("RGB", (400, 200), "red").save(png, "PNG")
        with mock.patch.object(image_store, "ASSETS_DIR", self.out.parent / "assets"):
            img = image_store.create("chip", png.getvalue(), {}).id
            asyncio.run(slides.make_slides.handler({"title": "Pics", "topic": "Logic gates", "slides": [
                {"title": "A chip", "points": ["A **CPU** is made of gates"], "picture": img},
                {"kind": "hook", "points": ["What's in a **CPU**?"]}]}))
        with mock.patch.object(slides, "LECTURES", self.out):
            self.assertIn("[picture]", slides.read_deck(self.out / "Pics.pptx")[1])
            text = asyncio.run(slides.make_slides.handler({"title": "Copy", "slides": [
                {"title": "Same chip", "figure": {"deck": "pics", "slide": 2}},
                {"title": "Gate", "figure": {"deck": "logic", "slide": 3}}]}))["content"][0]["text"]
            bad = asyncio.run(slides.make_slides.handler({"title": "Bad", "slides": [
                {"figure": {"deck": "pics", "slide": 9}}]}))
        self.assertIn("(4 slides)", text)
        self.assertIn("no slide 9", bad["content"][0]["text"])
        pics = Presentation(str(self.out / "Pics.pptx"))
        footer = [sh.text_frame.text for sh in pics.slides[1].slide_layout.shapes if sh.name.startswith("TextBox")]
        self.assertEqual(footer, ["\nPics"])  # a topic that isn't a number stays out of the header
        key = pics.slides[1].placeholders[14].text_frame.paragraphs[0].runs[1]
        self.assertEqual((key.text, key.font.color.rgb), ("CPU", slides.ACCENT))
        hook = pics.slides[2].placeholders[14].text_frame.paragraphs[0].runs[1]
        self.assertEqual((hook.font.bold, hook.font.color.type), (True, None))  # red on red would vanish
        copied = Presentation(str(self.out / "Copy.pptx")).slides
        self.assertEqual(copied[1].shapes[-1].image.blob[:4], b"\xff\xd8\xff\xe0")
        self.assertTrue(any(sh.has_table for sh in copied[2].shapes))
        ids = [sh.shape_id for sh in copied[2].shapes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_long_points_clear_the_teachers_figure(self):
        self.make()  # its slide 3 has a table under one short line
        long = ["A point long enough to wrap onto a second line of the slide, " * 2] * 15
        with mock.patch.object(slides, "LECTURES", self.out):
            text = asyncio.run(slides.make_slides.handler({"title": "Long", "slides": [
                {"title": "Gate", "points": long[:2], "figure": {"deck": "logic", "slide": 3}},
                {"title": "Gate", "points": long, "notes": "mine", "figure": {"deck": "logic", "slide": 3}}]}))
        self.assertIn("slide 3: 9 of its points", text["content"][0]["text"])
        for slide in list(Presentation(str(self.out / "Long.pptx")).slides)[1:3]:
            body = slide.placeholders[14]
            figure = min(sh.top for sh in slide.shapes if not sh.is_placeholder)
            self.assertLessEqual(body.top + body.height, figure)
        notes = Presentation(str(self.out / "Long.pptx")).slides[2].notes_slide.notes_text_frame.text
        self.assertTrue(notes.startswith("A point") and notes.endswith("mine"))

    def test_lectures_reads_a_deck(self):
        self.make()
        with mock.patch.object(slides, "LECTURES", self.out):
            listing = asyncio.run(slides.lectures.handler({}))["content"][0]["text"]
            text = asyncio.run(slides.lectures.handler({"deck": "logic"}))["content"][0]["text"]
        self.assertIn("Logic gates", listing)
        self.assertIn("--- Slide 3 (3_Custom Layout)", text)
        self.assertIn("A | B | Q", text)
        self.assertIn("Notes: What happens with 1 and 0?", text)
        self.assertEqual(registry.classify("mcp__jarvis__lectures"), "read")

    def test_lectures_pictures_skip_hidden_slides(self):
        self.make()
        path = self.out / "Logic gates.pptx"
        deck = Presentation(str(path))
        deck.slides[1]._element.set("show", "0")  # Keynote draws no picture for it
        deck.save(str(path))
        pictures = []
        for n in (1, 3, 4, 5):
            pictures.append(self.out / f"{n}.jpeg")
            pictures[-1].write_bytes(bytes([n]))
        with mock.patch.object(slides, "LECTURES", self.out), mock.patch.object(slides, "render", return_value=pictures):
            content = asyncio.run(slides.lectures.handler({"deck": "logic", "slides": [2, 3]}))["content"]
        self.assertEqual([c["type"] for c in content], ["text", "text", "text", "image"])
        self.assertIn("hidden", content[1]["text"])
        self.assertEqual(content[3]["data"], "Aw==")  # slide 3's picture


if __name__ == "__main__":
    unittest.main()
