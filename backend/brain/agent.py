"""Jarvis logic: router -> brain -> events."""

import logging
import time
import uuid
from contextlib import aclosing
from typing import AsyncIterator

import events
import hub
import usage
from config import GATEWAY_MODEL, NEW_CHAT_AFTER_IDLE_MIN
from tools import registry, web

from .base import Brain, Done, ModelAlias, TextDelta, ToolResult, ToolStart
from .router import STICKY_CONTEXT_TOKENS, Route, route

log = logging.getLogger("jarvis.agent")


class Jarvis:
    def __init__(self, brain: Brain) -> None:
        self.brain = brain

    def usage_event(self) -> events.Event:
        return events.usage_update(usage.snapshot(self.brain.provider, self.brain.context_tokens))

    def _idle_too_long(self) -> bool:
        """A big conversation left alone for over an hour: Claude's cached copy has
        expired, so continuing would send all of it again at full price."""
        if not NEW_CHAT_AFTER_IDLE_MIN or not self.brain.last_active:
            return False
        idle_s = time.time() - self.brain.last_active
        return idle_s > NEW_CHAT_AFTER_IDLE_MIN * 60 and self.brain.context_tokens > STICKY_CONTEXT_TOKENS

    async def handle_text(
        self,
        text: str,
        model_override: ModelAlias | None = None,
        voice: bool = False,
        selected_image: dict | None = None,
    ) -> AsyncIterator[events.Event]:
        """Answer one user message, yielding WebSocket events for the browser."""
        reply_id = uuid.uuid4().hex[:12]
        if self._idle_too_long():
            await self.brain.new_conversation()
            await hub.emit(events.conversation_new("idle"))
        if self.brain.provider == "omniroute":
            # Every model name goes to the one gateway model (see config.GATEWAY_MODEL).
            r = Route("sonnet", f"OmniRoute ({GATEWAY_MODEL})")
        else:
            r = route(text, model_override, voice, self.brain.model, self.brain.context_tokens)
        log.info("Route -> %s (%s)", r.model, r.reason)

        # Tell Claude what "this one" means when you've clicked an image.
        prompt = text
        if selected_image:
            prompt = (
                f"[On the canvas the user has selected image {selected_image['id']}, "
                f"showing v{selected_image['version']}.]\n{text}"
            )

        consulted_expert = False
        reply_text = ""
        tool_calls: dict[str, ToolStart] = {}  # tool id -> call
        looked_at: list[web.Source] = []  # pages the web tools saw

        async with aclosing(self.brain.send(prompt, model=r.model)) as stream:
            async for ev in stream:
                match ev:
                    case TextDelta():
                        reply_text += ev.text
                        yield events.from_brain(ev, reply_id)

                    case ToolStart():
                        label = registry.friendly_name(ev.name)
                        ev.name = registry.short_name(ev.name)
                        tool_calls[ev.id] = ev
                        consulted_expert |= ev.name == "ask_expert"
                        log.info("Tool %s %s", ev.name, web.tool_detail(ev.name, ev.input))
                        yield events.tool_started(
                            ev.id,
                            ev.name,
                            web.tool_detail(ev.name, ev.input),
                            label,
                        )

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
                        await hub.emit(self.usage_event())

                    case _:
                        yield events.from_brain(ev, reply_id)
