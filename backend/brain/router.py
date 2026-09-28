"""Haiku / Sonnet / Opus selection.

Order of checks:
  1. The model picked in the UI (manual override) always wins.
  2. Words in the message: "use opus", "think hard" -> Opus; "quick", "use haiku" -> Haiku.
  3. Small talk ("hi", "thanks", "how are you") -> Haiku. In voice mode, short messages too.
  4. Everything else -> Sonnet, which can call `ask_expert` to consult Opus.
"""

import re
from dataclasses import dataclass

from .base import ModelAlias


@dataclass(frozen=True)
class Route:
    model: ModelAlias
    reason: str  # shown in the UI so you can judge the routing


_FORCE_OPUS = re.compile(
    r"\b(use opus|with opus|think (really |very )?hard(er)?|think deeply|think carefully|deep dive)\b",
    re.IGNORECASE,
)
_FORCE_SONNET = re.compile(r"\b(use sonnet|with sonnet)\b", re.IGNORECASE)
_FORCE_HAIKU = re.compile(
    r"^\W*quick(ly)?\b|\b(use haiku|with haiku|quick (answer|question)|quickly)\b",
    re.IGNORECASE,
)

# Whole message is a greeting, thanks, acknowledgement or goodbye.
_SMALL_TALK = re.compile(
    r"^\W*("
    r"(hi|hey|hello|yo|hiya|howdy)( there)?( jarvis)?"
    r"|good (morning|afternoon|evening|night)( jarvis)?"
    r"|how are you( doing)?( today)?( jarvis)?|how's it going|what's up|sup"
    r"|(thanks|thank you|thx|ty|cheers)( (so|very) much)?( jarvis)?"
    r"|ok(ay)?|cool|nice|great|awesome|perfect|got it|sounds good|sure|yes|no|yep|nope"
    r"|bye|goodbye|see you( later)?|good ?night"
    r")\W*$",
    re.IGNORECASE,
)

VOICE_SHORT_WORDS = 6


def route(text: str, override: ModelAlias | None = None, voice: bool = False) -> Route:
    if override:
        return Route(override, "picked in the UI")

    if _FORCE_OPUS.search(text):
        return Route("opus", "you asked for deep thinking")
    if _FORCE_SONNET.search(text):
        return Route("sonnet", "you asked for Sonnet")
    if _FORCE_HAIKU.search(text):
        return Route("haiku", "you asked for a quick answer")

    if _SMALL_TALK.match(text):
        return Route("haiku", "small talk")
    if voice and len(text.split()) <= VOICE_SHORT_WORDS:
        return Route("haiku", "short voice message")

    return Route("sonnet", "default")
