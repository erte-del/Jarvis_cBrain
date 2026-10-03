"""Haiku / Sonnet / Opus selection.

Order of checks:
  1. The model picked in the UI (manual override) always wins.
  2. Words in the message: "use opus", "think hard" -> Opus; "quick", "use haiku" -> Haiku.
  3. Small talk ("hi", "thanks", "how are you") -> stays on the current model.
     In voice mode, short messages -> Haiku.
  4. Everything else -> Sonnet, which can call `ask_expert` to consult Opus.

Why small talk no longer goes to Haiku: each model keeps its own copy of the
conversation (the cache). Switching means sending the whole conversation to the other
model again, and even a fresh conversation is ~6-15K tokens. A short Haiku reply saves
far less than that, so the switch always cost more than it saved.

Sticky: for the same reason, once a conversation is bigger than STICKY_CONTEXT_TOKENS,
automatic picks never move it to a cheaper model (e.g. back from Opus to Sonnet).
Moving up from Haiku to Sonnet for a real question is still allowed.
Your own choices (1 and 2) always switch.
"""

import re
from dataclasses import dataclass

from .base import ModelAlias


@dataclass(frozen=True)
class Route:
    model: str  # a Claude alias, or a gateway model on OmniRoute
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
    r"(hi|hey|hello|yo|hiya|howdy)( there)?( ultron)?"
    r"|good (morning|afternoon|evening|night)( ultron)?"
    r"|how are you( doing)?( today)?( ultron)?|how's it going|what's up|sup"
    r"|(thanks|thank you|thx|ty|cheers)( (so|very) much)?( ultron)?"
    r"|ok(ay)?|cool|nice|great|awesome|perfect|got it|sounds good|sure|yes|no|yep|nope"
    r"|bye|goodbye|see you( later)?|good ?night"
    r")\W*$",
    re.IGNORECASE,
)

VOICE_SHORT_WORDS = 6


# A fresh conversation is ~6-15K tokens (instructions + tool lists), so this allows
# free switching for the first few messages only.
STICKY_CONTEXT_TOKENS = 20_000

_RANK: dict[str, int] = {"haiku": 0, "sonnet": 1, "opus": 2}


def route(
    text: str,
    override: ModelAlias | None = None,
    voice: bool = False,
    current: ModelAlias | None = None,
    context_tokens: int = 0,
) -> Route:
    if override:
        return Route(override, "picked in the UI")

    if _FORCE_OPUS.search(text):
        return Route("opus", "you asked for deep thinking")
    if _FORCE_SONNET.search(text):
        return Route("sonnet", "you asked for Sonnet")
    if _FORCE_HAIKU.search(text):
        return Route("haiku", "you asked for a quick answer")

    if _SMALL_TALK.match(text):
        auto = Route(current or "sonnet", "small talk: stayed on the same model")
    elif voice and len(text.split()) <= VOICE_SHORT_WORDS:
        auto = Route("haiku", "short voice message")
    else:
        auto = Route("sonnet", "default")

    cheaper = current is not None and _RANK[auto.model] < _RANK[current]
    if cheaper and context_tokens > STICKY_CONTEXT_TOKENS:
        return Route(current, f"stayed on {current.capitalize()}: switching would re-send the conversation")
    return auto
