"""Brain backed by Claude Code via the Agent SDK, using the Pro login.

One Claude Code process stays running for the whole conversation
(`ClaudeSDKClient`), so each message doesn't pay the startup cost.
"""

import asyncio
import logging
from typing import AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from config import STORAGE_DIR, use_pro_login

from .base import BrainEvent, Done, Error, ModelAlias, TextDelta, ToolResult, ToolStart
from .prompts import JARVIS_SYSTEM_PROMPT

log = logging.getLogger("jarvis.brain")

# Claude Code tools Jarvis must never have: it is an assistant, not a coding agent.
# If Claude Code sends nothing for this long, give up on the turn
# (e.g. it is silently retrying while Anthropic's servers are overloaded).
IDLE_TIMEOUT_S = 120

BLOCKED_TOOLS = [
    "Bash", "Read", "Write", "Edit", "MultiEdit", "NotebookEdit",
    "Glob", "Grep", "Agent", "Task", "Skill",
]


class ClaudeCodeBrain:
    def __init__(self, model: ModelAlias = "sonnet") -> None:
        self._model: ModelAlias = model
        self._client: ClaudeSDKClient | None = None
        self._lock = asyncio.Lock()  # one turn at a time
        self.auth_source: str | None = None  # reported by Claude Code at startup
        self._session_id: str | None = None  # lets a restarted process resume the conversation

    def _options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            system_prompt=JARVIS_SYSTEM_PROMPT,  # replaces Claude Code's coding prompt
            model=self._model,
            tools=[],  # no built-in tools yet (WebSearch/WebFetch come in Phase 3)
            disallowed_tools=BLOCKED_TOOLS,  # belt and braces
            include_partial_messages=True,  # stream text word by word
            setting_sources=[],  # ignore ~/.claude settings, CLAUDE.md files, plugins
            strict_mcp_config=True,  # only MCP servers Jarvis passes in (none yet)
            skills=[],
            cwd=STORAGE_DIR,
            resume=self._session_id,
        )

    async def _connect(self) -> ClaudeSDKClient:
        if self._client is None:
            use_pro_login()
            client = ClaudeSDKClient(self._options())
            await client.connect()
            self._client = client
            log.info("Claude Code session started (model=%s)", self._model)
        return self._client

    async def send(
        self,
        text: str,
        images: list[bytes] | None = None,
        model: ModelAlias = "sonnet",
    ) -> AsyncIterator[BrainEvent]:
        if images:
            raise NotImplementedError("Image input arrives in Phase 4")

        async with self._lock:
            finished = False
            try:
                client = await self._connect()
                if model != self._model:
                    await client.set_model(model)
                    self._model = model

                await client.query(text)

                answered_by = self._model
                messages = client.receive_response()
                while True:
                    try:
                        msg = await asyncio.wait_for(anext(messages), IDLE_TIMEOUT_S)
                    except StopAsyncIteration:
                        break
                    # Skip anything from sub-agents; Jarvis only shows its own reply.
                    if getattr(msg, "parent_tool_use_id", None):
                        continue

                    if isinstance(msg, StreamEvent):
                        ev = msg.event
                        if ev.get("type") == "content_block_delta":
                            delta = ev.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield TextDelta(delta["text"])

                    elif isinstance(msg, AssistantMessage):
                        answered_by = msg.model
                        if msg.error:  # reported to the UI via the ResultMessage below
                            log.warning("Claude error on %s: %s", msg.model, msg.error)
                        for block in msg.content:
                            if isinstance(block, ToolUseBlock):
                                yield ToolStart(block.id, block.name, block.input)

                    elif isinstance(msg, UserMessage) and isinstance(msg.content, list):
                        for block in msg.content:
                            if isinstance(block, ToolResultBlock):
                                yield ToolResult(block.tool_use_id, bool(block.is_error))

                    elif isinstance(msg, SystemMessage) and msg.subtype == "init":
                        self.auth_source = msg.data.get("apiKeySource")
                        self._session_id = msg.data.get("session_id")
                        log.info("Claude Code auth: apiKeySource=%s", self.auth_source)

                    elif isinstance(msg, ResultMessage):
                        finished = True
                        if msg.is_error:
                            detail = "; ".join(msg.errors or []) or msg.result or msg.subtype
                            yield Error(detail)
                        else:
                            yield Done(answered_by)
            except TimeoutError:
                log.error("No response from Claude Code for %ss; restarting session", IDLE_TIMEOUT_S)
                yield Error(f"No response for {IDLE_TIMEOUT_S}s. Claude may be overloaded; try again.")
            except Exception as e:  # keep the app alive; report to the UI
                log.exception("Brain turn failed")
                yield Error(f"{type(e).__name__}: {e}")
            finally:
                # If the turn was cut short (error, timeout, browser closed mid-reply),
                # Claude Code may still be sending the old reply. Restart it so the next
                # turn starts clean; `resume` keeps the conversation.
                if not finished:
                    await self.close()

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.disconnect()
            finally:
                self._client = None
