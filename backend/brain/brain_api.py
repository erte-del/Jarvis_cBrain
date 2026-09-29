"""Placeholder: API-key brain. Not used.

Jarvis runs on the Claude Pro subscription (see brain_claudecode.py).
If Jarvis ever switches to an API key, this class would implement the same
`Brain` protocol using the `anthropic` Python SDK. See section 1 of
JARVIS_BUILD_PROMPT.md for notes.
"""

from typing import AsyncIterator

from .base import BrainEvent, ModelAlias


class ApiBrain:
    def __init__(self) -> None:
        raise NotImplementedError("API brain not used; Jarvis runs on the Pro subscription")

    async def send(
        self,
        text: str,
        images: list[bytes] | None = None,
        model: ModelAlias = "sonnet",
    ) -> AsyncIterator[BrainEvent]:
        raise NotImplementedError("API brain not used; Jarvis runs on the Pro subscription")
        yield  # pragma: no cover  (makes this an async generator)

    async def new_conversation(self, provider: str | None = None) -> None:
        pass

    async def close(self) -> None:
        pass
