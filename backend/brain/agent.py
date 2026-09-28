"""Jarvis logic: router -> brain -> events."""

import logging
import uuid
from contextlib import aclosing
from typing import AsyncIterator

import events
from tools import registry, web

from .base import Brain, Done, ModelAlias, TextDelta, ToolResult, ToolStart
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
        reply_text = ""
        tool_calls: dict[str, ToolStart] = {}  # tool id -> call
        looked_at: list[web.Source] = []  # pages the web tools saw

        async with aclosing(self.brain.send(text, model=r.model)) as stream:
            async for ev in stream:
                match ev:
                    case TextDelta():
                        reply_text += ev.text
                        yield events.from_brain(ev, reply_id)

                    case ToolStart():
                        ev.name = registry.short_name(ev.name)
                        tool_calls[ev.id] = ev
                        consulted_expert |= ev.name == "ask_expert"
                        log.info("Tool %s %s", ev.name, web.tool_detail(ev.name, ev.input))
                        yield events.tool_started(ev.id, ev.name, web.tool_detail(ev.name, ev.input))

                    case ToolResult():
                        call = tool_calls.get(ev.id)
                        if call and not ev.is_error:
                            looked_at += web.sources_from_result(call.name, call.input, ev.data)
                        yield events.from_brain(ev, reply_id)

                    case Done():
                        sources = web.pick_sources(reply_text, looked_at)
                        yield events.done(
                            reply_id, ev.model, r.model, r.reason, consulted_expert, sources
                        )

                    case _:
                        yield events.from_brain(ev, reply_id)
