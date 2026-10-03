"""Textbook: page lookup over saved OCR text. No PDF or tesseract needed.
    .venv/bin/python -m unittest tests.test_textbook
"""

import unittest

from tools import registry, textbook

# Printed pages 1-30 after a cover and contents, but the scan skipped page 11; page 5 has
# an exercise number after its page number.
NUMS = [n for n in range(1, 31) if n != 11]
PAGES = ["Cover", "Contents\n1 Algebra 1"] + [f"Text\n{n}" for n in NUMS]
PAGES[2 + 4] = "Exercise 1A\n5\n3"
PAGES[2 + 20] = "Discriminant\n22"


class TextbookTest(unittest.TestCase):
    def test_runs_freely(self):
        self.assertEqual(registry.classify("mcp__ultron__textbook"), "read")

    def test_printed(self):
        self.assertEqual(textbook.printed(PAGES)[2:], NUMS)

    def test_pick(self):
        self.assertEqual(textbook.pick(PAGES, "", None), [1])  # contents
        self.assertEqual(textbook.pick(PAGES, "discriminant", None), [22])
        self.assertEqual(textbook.pick(PAGES, "", 12), [12, 13])  # printed page and the next
        self.assertEqual(textbook.pick(PAGES, "", 10), [11])  # 11 isn't in the scan


if __name__ == "__main__":
    unittest.main()
