"""Telegram: only your own chat, no asking, errors never show the token. Nothing is really sent.
    .venv/bin/python -m unittest tests.test_telegram
"""

import asyncio
import io
import unittest
from unittest import mock
from urllib.error import HTTPError

import config
from tools import registry, telegram

TOKEN = "123:secret"


def send(args, urlopen=None, token=TOKEN, chat_id="42"):
    urlopen = urlopen or mock.MagicMock()
    urlopen.return_value.__enter__.return_value = io.BytesIO(b'{"ok": true, "result": {}}')
    with mock.patch.object(config, "TELEGRAM_BOT_TOKEN", token, create=True), \
            mock.patch.object(config, "TELEGRAM_CHAT_ID", chat_id, create=True), \
            mock.patch.object(telegram, "urlopen", urlopen):
        return asyncio.run(telegram.text_me.handler(args)), urlopen


class TelegramTest(unittest.TestCase):
    def test_runs_without_asking(self):
        self.assertEqual(registry.classify("mcp__jarvis__text_me"), "read")

    def test_sends_to_the_chat_in_env_only(self):
        result, urlopen = send({"message": "Meeting in 10 min", "chat_id": "999"})
        req = urlopen.call_args.args[0]
        self.assertEqual(req.full_url, f"https://api.telegram.org/bot{TOKEN}/sendMessage")
        self.assertEqual(req.data, b'{"chat_id": "42", "text": "Meeting in 10 min"}')
        self.assertNotIn("is_error", result)

    def test_nothing_sent_when_not_set_up_empty_or_too_long(self):
        for args, kwargs in [({"message": "hi"}, {"token": ""}), ({"message": "hi"}, {"chat_id": ""}),
                             ({"message": "  "}, {}), ({"message": "x" * 4097}, {})]:
            result, urlopen = send(args, **kwargs)
            self.assertTrue(result["is_error"], (args, kwargs))
            urlopen.assert_not_called()

    def test_errors_never_show_the_token(self):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        error = HTTPError(url, 401, "Unauthorized", {}, io.BytesIO(b'{"ok": false, "description": "Unauthorized"}'))
        result, _ = send({"message": "hi"}, mock.MagicMock(side_effect=error))
        self.assertTrue(result["is_error"])
        self.assertIn("Unauthorized", result["content"][0]["text"])
        self.assertNotIn("secret", result["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
