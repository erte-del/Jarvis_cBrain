"""Amazon: which pages it opens, which buttons it presses, never checkout. Chrome isn't touched.
    .venv/bin/python -m unittest tests.test_amazon
"""

import asyncio
import unittest
from unittest import mock

import config
from tools import amazon, registry


class AmazonTest(unittest.TestCase):
    def call(self, handler, where="", text="Amazon\nsome page", **args):
        async def fake_run(url, javascript, opened="tab", reuse=True):
            self.url, self.javascript = url, javascript
            return where or url, text

        self.url = None
        with mock.patch.object(amazon, "_run", fake_run):
            return asyncio.run(handler.handler(args))

    def test_reading_runs_freely_and_changing_asks(self):
        self.assertEqual(registry.classify("mcp__jarvis__amazon_read"), "read")
        self.assertEqual(registry.classify("mcp__jarvis__amazon_change"), "act")

    def test_pages(self):
        self.call(amazon.amazon_read, search="usb c cable & hub")
        self.assertEqual(self.url, config.AMAZON_URL + "/s?k=usb+c+cable+%26+hub")
        self.call(amazon.amazon_read, page="Orders")
        self.assertEqual(self.url, config.AMAZON_URL + "/gp/css/order-history")
        self.call(amazon.amazon_read, page="B01GGKYXVE")
        self.assertEqual(self.url, config.AMAZON_URL + "/dp/B01GGKYXVE")

    def test_never_leaves_amazon_or_opens_checkout(self):
        for page in (".evil.example/x", "@evil.example/x", "https://evil.example", "/gp/buy/spc/handlers/display.html",
                     "/checkout/p/1", "/ap/signin"):
            result = self.call(amazon.amazon_read, page=page)
            self.assertTrue(result["is_error"], page)
            self.assertIsNone(self.url, page)  # Chrome was never asked
        self.call(amazon.amazon_read, page="//evil.example/x")  # just an odd path on Amazon
        self.assertTrue(self.url.startswith(config.AMAZON_URL + "/"))

    def test_only_the_three_buttons(self):
        self.assertEqual(set(amazon.ACTIONS), {"add_to_cart", "remove_from_cart", "add_to_list"})
        for action in ("buy_now", "place_order", ""):
            self.assertTrue(self.call(amazon.amazon_change, action=action, asin="B01GGKYXVE", title="x")["is_error"])
            self.assertIsNone(self.url)
        # The ASIN goes into a selector, so it has to be an ASIN.
        self.assertTrue(self.call(amazon.amazon_change, action="remove_from_cart", asin='x"] , #buy-now-button', title="x")["is_error"])
        self.assertIsNone(self.url)

    def test_add_to_cart(self):
        result = self.call(amazon.amazon_change, text="Added to cart", action="add_to_cart", asin="b01ggkyxve", title="Cable", quantity=2)
        self.assertEqual(self.url, config.AMAZON_URL + "/dp/B01GGKYXVE")
        self.assertTrue(self.javascript.endswith('("#add-to-cart-button", 2)'))
        self.assertIn("Added to cart", result["content"][0]["text"])
        missing = self.call(amazon.amazon_change, text="CANT\nCurrently unavailable", action="add_to_cart", asin="B01GGKYXVE", title="Cable")
        self.assertTrue(missing["is_error"])
        self.assertIn("nothing was changed", missing["content"][0]["text"])

    def test_signed_out_is_explained(self):
        result = self.call(amazon.amazon_read, where=config.AMAZON_URL + "/ap/signin?x=1", text="Sign in", page="orders")
        self.assertTrue(result["is_error"])
        self.assertIn("isn't signed in", result["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
