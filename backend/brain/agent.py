"""Jarvis logic: router -> brain -> events."""

import logging
import uuid
from contextlib import aclosing
from typing import AsyncIterator

import events
from tools import registry

from .base import Brain, Done, ModelAlias, ToolStart
from .router import route

log = logging.getLogger("jarvis.agent")


class Jarvis:
    def __init__(self, brain: Brain) -> None:
        self.brain = brain

    async def handle_text(
        self,
        text: str,
        model_override: ModelAlias | None = None,
        voice: bool = False,
    ) -> AsyncIterator[events.Event]:
        """Answer one user message, yielding WebSocket events for the browser."""
        reply_id = uuid.uuid4().hex[:12]
        r = route(text, model_override, voice)
        log.info("Route -> %s (%s)", r.model, r.reason)
        consulted_expert = False

        async with aclosing(self.brain.send(text, model=r.model)) as stream:
            async for ev in stream:
                if isinstance(ev, ToolStart):
                    ev.name = registry.short_name(ev.name)
                    if ev.name == "ask_expert":
                        consulted_expert = True
                if isinstance(ev, Done):
                    yield events.done(reply_id, ev.model, r.model, r.reason, consulted_expert)
                else:
                    yield events.from_brain(ev, reply_id)
