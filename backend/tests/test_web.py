"""Web helper tests. Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import asyncio
import unittest

from tools.web import is_public_url, links_in_text, pick_sources, sources_from_result


class PublicUrlTest(unittest.TestCase):
    def ok(self, url: str) -> bool:
        return asyncio.run(is_public_url(url))[0]

    def test_blocks_local_and_private(self):
        for url in [
            "http://127.0.0.1:8000/health",
            "http://localhost:5173",
            "http://192.168.1.1/admin",
            "http://10.0.0.5",
            "http://172.16.0.1",
            "http://169.254.169.254/latest/meta-data",
            "http://[::1]/",
            "http://router/",
            "http://printer.local/",
            "file:///etc/passwd",
            "ftp://example.com/file",
        ]:
            self.assertFalse(self.ok(url), url)

    def test_allows_public_ip(self):
        self.assertTrue(self.ok("https://1.1.1.1/"))


class SourcesTest(unittest.TestCase):
    looked_at = [
        {"title": "Result A", "url": "https://a.com/x"},
        {"title": "Result B", "url": "https://b.com/y"},
        {"title": "Result C", "url": "https://c.com"},
        {"title": "Result D", "url": "https://d.com"},
        {"title": "", "url": "https://f1.com/results"},  # a fetched page
    ]

    def test_prefers_cited_links(self):
        reply = "Russell won.\n\nSources:\n- [F1 results](https://f1.com/results)\n- [B](https://b.com/y)"
        urls = [s["url"] for s in pick_sources(reply, self.looked_at)]
        self.assertEqual(urls, ["https://f1.com/results", "https://b.com/y"])

    def test_falls_back_to_fetched_then_top_results(self):
        urls = [s["url"] for s in pick_sources("Russell won.", self.looked_at)]
        self.assertEqual(urls, ["https://f1.com/results", "https://a.com/x", "https://b.com/y", "https://c.com"])

    def test_no_web_tools_no_sources(self):
        self.assertEqual(pick_sources("see [x](https://x.com)", []), [])

    def test_links_in_text(self):
        links = links_in_text("Read [this](https://a.com/p) or https://b.com/q.")
        self.assertEqual([l["url"] for l in links], ["https://a.com/p", "https://b.com/q"])

    def test_search_result_shape(self):
        data = {"query": "q", "results": [{"tool_use_id": "x", "content": [{"title": "T", "url": "https://t.com"}]}]}
        self.assertEqual(sources_from_result("WebSearch", {}, data), [{"title": "T", "url": "https://t.com"}])
        self.assertEqual(
            sources_from_result("WebFetch", {"url": "https://u.com"}, {"url": "https://u.com"}),
            [{"title": "", "url": "https://u.com"}],
        )


if __name__ == "__main__":
    unittest.main()
