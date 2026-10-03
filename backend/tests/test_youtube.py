"""YouTube: the search it fetches, how it reads the page, what it refuses. Nothing is fetched.
    .venv/bin/python -m unittest tests.test_youtube
"""

import asyncio
import json
import unittest
from unittest import mock

from tools import registry, youtube

VIDEO = {"videoId": "dQw4w9WgXcQ", "title": {"runs": [{"text": "Never Gonna Give You Up"}]},
         "ownerText": {"runs": [{"text": "Rick Astley"}]}, "lengthText": {"simpleText": "3:33"},
         "viewCountText": {"simpleText": "1,700,000,000 views"}, "publishedTimeText": {"simpleText": "16y ago"}}
# Results sit in shelves nested anywhere; a repeat and a bad id are dropped.
DATA = {"contents": [{"videoRenderer": VIDEO}, {"shelf": {"items": [{"videoRenderer": VIDEO},
        {"videoRenderer": {**VIDEO, "videoId": "x\" onclick=1"}}]}}]}
PAGE = f"<script>var ytInitialData = {json.dumps(DATA)};</script><script>var x = {{}};</script>"


class YoutubeTest(unittest.TestCase):
    def call(self, page=PAGE, **args):
        async def fake_fetch(url):
            self.url = url
            return page

        self.url = None
        with mock.patch.object(youtube, "_fetch", fake_fetch):
            return asyncio.run(youtube.youtube.handler(args))

    def test_only_reads(self):
        self.assertEqual(registry.classify("mcp__ultron__youtube"), "read")

    def test_search(self):
        result = self.call(query="rick astley & friends")
        self.assertEqual(self.url, "https://www.youtube.com/results?search_query=rick+astley+%26+friends&hl=en")
        lines = result["content"][0]["text"].splitlines()
        self.assertEqual(lines[0], "https://www.youtube.com/watch?v=dQw4w9WgXcQ | Never Gonna Give You Up | "
                                   "Rick Astley | 3:33 | 1,700,000,000 views | 16y ago")
        self.assertEqual(sum("watch?v=" in line for line in lines), 1)

    def test_refuses_empty_query_and_empty_page(self):
        self.assertTrue(self.call(query="  ")["is_error"])
        self.assertIsNone(self.url)  # nothing was fetched
        self.assertTrue(self.call(page="<html>consent</html>", query="x")["is_error"])

    def test_canvas_card_only_takes_video_ids(self):
        from tools import canvas
        card = canvas._card_data({"kind": "youtube", "items": [
            {"id": "dQw4w9WgXcQ", "title": "Never", "length": "3:33", "url": "https://evil.example"},
            {"id": "../../evil?x=1", "title": "Bad"}]})
        self.assertEqual(card, {"items": [{"id": "dQw4w9WgXcQ", "title": "Never", "length": "3:33"}]})
        with self.assertRaises(ValueError):
            canvas._card_data({"kind": "youtube", "items": [{"id": "nope"}]})


if __name__ == "__main__":
    unittest.main()
