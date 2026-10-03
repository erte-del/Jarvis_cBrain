"""Syllabus: page search over a saved spec. The exam boards aren't contacted.
    .venv/bin/python -m unittest tests.test_syllabus
"""

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import registry, syllabus

PAGES = ["Contents", "Content overview\nTopic 1 Proof", "Topic 2 Algebra", "Hash tables: hashing, collisions",
         "Hash tables again; tables of tables"]


class SyllabusTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patch = mock.patch.object(syllabus, "DIR", Path(tmp.name))
        patch.start()
        self.addCleanup(patch.stop)
        (Path(tmp.name) / "computer_science.txt").write_text(syllabus.PAGE.join(PAGES))

    def ask(self, **args):
        return asyncio.run(syllabus.syllabus.handler(args))["content"][0]["text"]

    def test_runs_freely(self):
        self.assertEqual(registry.classify("mcp__ultron__syllabus"), "read")

    def test_find(self):
        self.assertEqual(syllabus.find(PAGES, ""), [1, 2])  # overview and the page after
        self.assertEqual(syllabus.find(PAGES, "hash tables"), [4, 3])  # most hits first
        self.assertEqual(syllabus.find(PAGES, "quantum"), [])

    def test_answer(self):
        text = self.ask(subject="computer_science", query="collisions")
        self.assertIn("AQA", text)
        self.assertIn("[spec page 4]\nHash tables: hashing, collisions", text)
        self.assertIn("adacomputerscience.org", text)
        self.assertIn("probably not on this course", self.ask(subject="computer_science", query="quantum"))
        self.assertIn("Unknown subject", self.ask(subject="history"))


if __name__ == "__main__":
    unittest.main()
