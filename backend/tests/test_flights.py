"""Flights: the search it opens, what it refuses. Chrome isn't touched.
    .venv/bin/python -m unittest tests.test_flights
"""

import asyncio
import datetime as dt
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlsplit

from tools import flights, registry

SOON = str(dt.date.today() + dt.timedelta(days=30))
LATER = str(dt.date.today() + dt.timedelta(days=37))


class FlightsTest(unittest.TestCase):
    def call(self, text="Dubai to Istanbul | Google Flights\nFrom 824 UAE dirhams. Nonstop flight with Pegasus.", **args):
        async def fake_run(url, javascript, opened="tab", reuse=True):
            self.url = url
            return url, text

        self.url = None
        with mock.patch.object(flights, "_run", fake_run):
            return asyncio.run(flights.flights.handler(args))

    def query(self):
        return parse_qs(urlsplit(self.url).query)["q"][0]

    def test_only_reads(self):
        self.assertEqual(registry.classify("mcp__ultron__flights"), "read")

    def test_round_trip_and_one_way(self):
        result = self.call(**{"from": "DXB", "to": "Istanbul", "depart": SOON, "return": LATER})
        self.assertTrue(self.url.startswith("https://www.google.com/travel/flights?"))
        self.assertEqual(self.query(), f"Flights from DXB to Istanbul on {SOON} returning {LATER} for 1 adults economy class")
        self.assertIn("Pegasus", result["content"][0]["text"])
        self.assertIn(self.url, result["content"][0]["text"])
        self.call(**{"from": "DXB", "to": "LHR", "depart": SOON, "adults": 2, "cabin": "business"})
        self.assertEqual(self.query(), f"Flights from DXB to LHR on {SOON} one way for 2 adults business class")

    def test_refuses_bad_searches(self):
        past = str(dt.date.today() - dt.timedelta(days=1))
        for args in ({"to": "LHR", "depart": SOON}, {"from": "DXB", "to": "LHR", "depart": "next friday"},
                     {"from": "DXB", "to": "LHR", "depart": past},
                     {"from": "DXB", "to": "LHR", "depart": LATER, "return": SOON},
                     {"from": "DXB", "to": "LHR", "depart": SOON, "adults": 12},
                     {"from": "DXB", "to": "LHR", "depart": SOON, "cabin": "cargo"}):
            self.assertTrue(self.call(**args)["is_error"], args)
            self.assertIsNone(self.url, args)  # Chrome was never asked

    def test_empty_page(self):
        self.assertTrue(self.call(text="", **{"from": "DXB", "to": "LHR", "depart": SOON})["is_error"])


if __name__ == "__main__":
    unittest.main()
