"""Homework: what's new, read-only label, errors. Chrome itself isn't touched.
    .venv/bin/python -m unittest tests.test_homework
"""

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import config
from tools import homework, registry


class HomeworkTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patch = mock.patch.object(homework, "SEEN_FILE", Path(tmp.name) / "seen.json")
        patch.start()
        self.addCleanup(patch.stop)

    def check(self, where, text):
        async def fake_run(url):
            return where, text

        with mock.patch.object(homework, "_run", fake_run):
            return asyncio.run(homework.check_homework.handler({}))

    def test_runs_freely(self):
        self.assertEqual(registry.classify("mcp__jarvis__check_homework"), "read")

    def test_only_new_lines_are_reported(self):
        first = self.check(config.HOMEWORK_URL, "Maths\nAlgebra sheet\nDue Friday")["content"][0]["text"]
        self.assertIn("first check", first)
        same = self.check(config.HOMEWORK_URL, "Maths\nAlgebra sheet\nDue Friday")["content"][0]["text"]
        self.assertIn("Nothing in the feed has changed", same)
        more = self.check(config.HOMEWORK_URL, "Maths\nAlgebra sheet\nDue Friday\nPhysics\nForces quiz")
        self.assertTrue(more["content"][0]["text"].endswith("since the last check:\nPhysics\nForces quiz"))

    def test_signed_out_is_explained(self):
        result = self.check("https://login.microsoftonline.com/common/oauth2", "Sign in")
        self.assertTrue(result["is_error"])
        self.assertIn("isn't signed in", result["content"][0]["text"])
        self.assertFalse(homework.SEEN_FILE.exists())  # the login page isn't remembered as homework

    def test_chrome_setting_is_explained(self):
        async def refused(url):
            raise RuntimeError("Chrome doesn't let Jarvis read pages yet.")

        with mock.patch.object(homework, "_run", refused):
            result = asyncio.run(homework.check_homework.handler({}))
        self.assertTrue(result["is_error"])
        self.assertIn("doesn't let Jarvis", result["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
