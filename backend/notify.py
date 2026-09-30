"""Reaching you when you're not looking at the chat.

One notification goes three ways:
  - the open Jarvis tabs (it appears in the chat),
  - a macOS notification on this Mac,
  - a text to your phone from Jarvis's Telegram bot, if it's set up (.env.example).

Jarvis's conversation didn't write these (a scheduled job did), so the next message you
send carries them along (`take_unseen`): "reply to that tonight" then means something.
"""

import asyncio
import logging
import time

import events
import hub
from tools import telegram

log = logging.getLogger("jarvis.notify")

MAC_CHARS = 240  # a banner shows about this much
MAX_UNSEEN = 5

# The text reaches the script as arguments, never pasted into its source.
MAC_SCRIPT = 'on run argv\ndisplay notification (item 1 of argv) with title (item 2 of argv) sound name "Glass"\nend run'

_unseen: list[str] = []


async def _mac(title: str, text: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "osascript", "-e", MAC_SCRIPT, text[:MAC_CHARS], title,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    if await asyncio.wait_for(proc.wait(), timeout=10):
        raise OSError("osascript couldn't show the notification")


async def push(title: str, text: str) -> None:
    """Tell the user something. A channel that fails is logged, never raised."""
    _unseen.append(f"{title}: {text}")
    del _unseen[:-MAX_UNSEEN]
    await hub.emit(events.notification(title, text, time.time()))
    try:
        await _mac(title, text)
    except (OSError, TimeoutError):
        log.warning("macOS notification failed", exc_info=True)
    if telegram.configured():
        try:
            await asyncio.to_thread(telegram.send_text, f"{title}\n\n{text}")
        except RuntimeError as e:  # never includes the bot token
            log.warning("Telegram notification failed: %s", e)


def take_unseen() -> list[str]:
    """Notifications since the user's last message, for Jarvis's conversation to know about."""
    seen = _unseen[:]
    _unseen.clear()
    return seen
