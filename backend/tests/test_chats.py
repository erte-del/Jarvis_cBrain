"""Saved chats: the 5-chat limit. Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from storage import chat_store

MESSAGES = [{"role": "user", "text": "Plan my  trip"}, {"role": "assistant", "text": "Sure", "model": "sonnet"},
            {"role": "confirm", "text": ""}]
CARDS = [{"id": "card_4", "kind": "table", "title": "Flights", "data": {"columns": ["a"], "rows": []}},
         {"id": "img_001", "kind": "image", "title": "Beach", "data": {"versions": ["big"]}}]


class ChatStoreTest(unittest.TestCase):
    def setUp(self):
        patch = mock.patch.object(chat_store, "CHATS_FILE", Path(tempfile.mkdtemp()) / "chats.json")
        patch.start()
        self.addCleanup(patch.stop)

    def test_save_load_delete(self):
        chat_store.save("s1", "claude", MESSAGES, CARDS)
        chat = chat_store.load("s1")
        self.assertEqual(chat["title"], "Plan my trip")
        self.assertEqual([m["role"] for m in chat["messages"]], ["user", "assistant"])
        # an image card keeps only its id: it's rebuilt from the image store on load
        self.assertEqual(chat["cards"][1], {"id": "img_001", "kind": "image", "title": "Beach"})
        self.assertEqual(chat["cards"][0]["data"]["columns"], ["a"])
        chat_store.delete("s1")
        self.assertEqual(chat_store.summaries(), [])

    def test_at_most_five_but_updates_still_work(self):
        for i in range(chat_store.MAX_CHATS):
            chat_store.save(f"s{i}", "claude", MESSAGES, [])
        with self.assertRaises(ValueError):
            chat_store.save("new", "claude", MESSAGES, [])
        chat_store.save("s0", "claude", MESSAGES, [])  # re-saving an existing chat is fine
        self.assertEqual(len(chat_store.summaries()), chat_store.MAX_CHATS)
        chat_store.delete("s1")
        chat_store.save("new", "claude", MESSAGES, [])
        self.assertEqual(chat_store.summaries()[0]["id"], "new")


if __name__ == "__main__":
    unittest.main()
