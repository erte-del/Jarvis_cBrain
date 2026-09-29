"""Contacts: relationship words, read-only label, errors. The Contacts app itself isn't touched.
    .venv/bin/python -m unittest tests.test_contacts
"""

import asyncio
import json
import unittest
from unittest import mock

from tools import contacts, registry


class ContactsTest(unittest.TestCase):
    def test_relationship_words(self):
        self.assertEqual(contacts.relation_label("my mom"), "mother")
        self.assertEqual(contacts.relation_label("Mum"), "mother")
        self.assertEqual(contacts.relation_label("my boss"), "manager")
        self.assertIsNone(contacts.relation_label("Sarah"))

    def test_lookup_runs_freely(self):
        self.assertEqual(registry.classify("mcp__jarvis__find_contact"), "read")

    def test_mom_goes_through_my_card(self):
        calls = []

        async def fake_run(mode, query):
            calls.append((mode, query))
            return "Jane Doe" if mode == "related" else {"term": "Jane Doe", "people": [{"name": "Jane Doe"}]}

        with mock.patch.object(contacts, "_run", fake_run):
            result = asyncio.run(contacts.find_contact.handler({"query": "my mom"}))
        self.assertEqual(calls, [("related", "mother"), ("search", '{"terms": ["Jane Doe"], "exclude": []}')])
        self.assertIn("Jane Doe", result["content"][0]["text"])

    def test_search_order_english_then_turkish_then_others(self):
        terms = contacts.search_terms("mother", "my mom")
        self.assertEqual(terms[:2], ["mom", "mum"])
        self.assertLess(terms.index("mother"), terms.index("annem"))
        self.assertLess(terms.index("annem"), terms.index("anne"))  # longer word first
        self.assertLess(terms.index("anne"), terms.index("mamá"))
        self.assertEqual(contacts.relation_label("Annem"), "mother")

    def test_without_my_card_words_are_searched_in_order(self):
        calls = []

        async def fake_run(mode, query):
            calls.append((mode, query))
            if mode == "related":
                return None
            return {"term": "annem", "people": [{"name": "Annemmmmmmm"}]}

        with mock.patch.object(contacts, "_run", fake_run):
            result = asyncio.run(contacts.find_contact.handler({"query": "my mom"}))
        sent = json.loads(calls[1][1])
        self.assertEqual(sent["terms"], contacts.search_terms("mother", "mom"))
        self.assertIn("anneanne", sent["exclude"])  # "Anneannem" is grandma, not mom
        self.assertIn("Found by searching 'annem'", result["content"][0]["text"])

    def test_permission_error_is_explained(self):
        async def denied(mode, query):
            raise RuntimeError("macOS didn't allow Jarvis to use Contacts.")

        with mock.patch.object(contacts, "_run", denied):
            result = asyncio.run(contacts.find_contact.handler({"query": "Sarah"}))
        self.assertTrue(result["is_error"])
        self.assertIn("didn't allow", result["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
