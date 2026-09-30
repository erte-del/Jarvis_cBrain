"""Telegram: Jarvis texts you from its own bot, which shows up on your phone as a separate
"Jarvis" chat. (read: it can only reach your own chat)

The chat it writes to is fixed in .env (TELEGRAM_CHAT_ID), so whatever Jarvis is told, a
message can't go to anyone else. Setup is in .env.example. To find your chat id, message
the bot once, then run:
    .venv/bin/python -m tools.telegram

Jarvis can't read what you reply yet, and a bot can't place calls.
"""

import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from claude_agent_sdk import tool

import config

API = "https://api.telegram.org/bot{token}/{method}"
MAX_CHARS = 4096  # Telegram's limit for one message


def _call(method: str, params: dict[str, Any]) -> Any:
    # The token is part of the address, so errors must never include the URL.
    req = Request(API.format(token=config.TELEGRAM_BOT_TOKEN, method=method),
                  data=json.dumps(params).encode(), headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=20) as r:
            return json.load(r)["result"]
    except HTTPError as e:
        try:
            why = json.load(e)["description"]
        except (ValueError, KeyError):
            why = f"HTTP {e.code}"
        raise RuntimeError(why) from None
    except (URLError, TimeoutError) as e:
        raise RuntimeError(f"couldn't reach Telegram ({getattr(e, 'reason', e)})") from None


def _text(text: str, is_error: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["is_error"] = True
    return result


def configured() -> bool:
    return bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)


def send_text(message: str) -> None:
    """Text your own chat (blocking). RuntimeError with the reason if it didn't go."""
    _call("sendMessage", {"chat_id": config.TELEGRAM_CHAT_ID, "text": message[:MAX_CHARS]})


@tool(
    "text_me",
    "Text the user on their phone, from Jarvis's own Telegram bot. It only ever goes to "
    "the user themselves; to message anyone else use whatsapp_send or email. Can't read replies.",
    {
        "type": "object",
        "properties": {"message": {"type": "string", "description": "The text to send, plain text."}},
        "required": ["message"],
    },
)
async def text_me(args: dict[str, Any]) -> dict[str, Any]:
    message = str(args.get("message") or "").strip()
    if not configured():
        return _text("Telegram isn't set up: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env "
                     "(steps in .env.example). Not sent.", True)
    if not message:
        return _text("The message is empty; not sent.", True)
    if len(message) > MAX_CHARS:
        return _text(f"Too long for one text ({len(message)} characters, the limit is {MAX_CHARS}); not sent.", True)
    try:
        await asyncio.to_thread(send_text, message)
    except RuntimeError as e:
        return _text(f"Telegram: {e}. Not sent.", True)
    return _text("Sent to the user's phone.")


if __name__ == "__main__":  # setup helper: who has messaged the bot?
    if not config.TELEGRAM_BOT_TOKEN:
        raise SystemExit("Put TELEGRAM_BOT_TOKEN in .env first.")
    chats = {u["message"]["chat"]["id"]: u["message"]["chat"].get("first_name", "")
             for u in _call("getUpdates", {}) if "message" in u}
    if not chats:
        raise SystemExit("Nobody has messaged the bot yet. Open it in Telegram, press Start, run this again.")
    for chat_id, name in chats.items():
        print(f"TELEGRAM_CHAT_ID={chat_id}   ({name})")
