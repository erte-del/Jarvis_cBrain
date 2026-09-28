"""Brain protocol + BrainEvent types.

Everything in Jarvis talks to a `Brain`, never to Claude Code or the API
directly. That way the brain can be swapped (Pro subscription today,
API key someday) without touching the rest of the app.
"""

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Literal, Protocol

ModelAlias = Literal["haiku", "sonnet", "opus"]


@dataclass
class TextDelta:
    """A small piece of the reply text, streamed as it is generated."""
    text: str
    type: Literal["text_delta"] = "text_delta"


@dataclass
class ToolStart:
    """Claude started using a tool (e.g. a web search)."""
    id: str
    name: str
    input: dict[str, Any] = field(default_factory=dict)
    type: Literal["tool_start"] = "tool_start"


@dataclass
class ToolResult:
    """A tool finished. `data` is the tool's structured result, when there is one."""
    id: str
    is_error: bool = False
    data: Any = None
    type: Literal["tool_result"] = "tool_result"


@dataclass
class UIEvent:
    """Something for the frontend to show (canvas image, card, ...). Phase 4+."""
    name: str
    data: dict[str, Any] = field(default_factory=dict)
    type: Literal["ui_event"] = "ui_event"


@dataclass
class Done:
    """The reply is complete. `model` is the full model ID that answered."""
    model: str
    type: Literal["done"] = "done"


@dataclass
class Error:
    message: str
    type: Literal["error"] = "error"


BrainEvent = TextDelta | ToolStart | ToolResult | UIEvent | Done | Error


class Brain(Protocol):
    async def send(
        self,
        text: str,
        images: list[bytes] | None = None,
        model: ModelAlias = "sonnet",
    ) -> AsyncIterator[BrainEvent]:
        """Send one user message and stream back events until `Done` or `Error`."""
        ...

    async def close(self) -> None:
        """Release resources (e.g. stop the Claude Code process)."""
        ...
