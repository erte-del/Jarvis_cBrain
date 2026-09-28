"""WebSocket event types — the shared protocol with frontend/src/ws.ts.

Every message is a JSON object with a "type" field.

Client -> server (Phase 1):
    user.text        {text}
    settings.update  {model_override: "haiku" | "sonnet" | "opus" | null}

Server -> client (Phase 1):
    status               {state: "idle" | "thinking"}
    assistant.text_delta {id, text}       id = the reply this text belongs to
    assistant.done       {id, model}      model = full model ID that answered
    tool.started         {id, name}
    tool.finished        {id, is_error}
    error                {message, id?}

Later phases add user.audio_*, user.confirm, canvas.*, confirm.request, ...
"""

from typing import Any

from brain.base import BrainEvent, Done, Error, TextDelta, ToolResult, ToolStart, UIEvent

Event = dict[str, Any]


def status(state: str) -> Event:
    return {"type": "status", "state": state}


def error(message: str, reply_id: str | None = None) -> Event:
    ev: Event = {"type": "error", "message": message}
    if reply_id:
        ev["id"] = reply_id
    return ev


def from_brain(ev: BrainEvent, reply_id: str) -> Event:
    """Translate a brain event into the WebSocket event the frontend understands."""
    match ev:
        case TextDelta(text=text):
            return {"type": "assistant.text_delta", "id": reply_id, "text": text}
        case Done(model=model):
            return {"type": "assistant.done", "id": reply_id, "model": model}
        case ToolStart(id=tool_id, name=name):
            return {"type": "tool.started", "id": tool_id, "name": name}
        case ToolResult(id=tool_id, is_error=is_error):
            return {"type": "tool.finished", "id": tool_id, "is_error": is_error}
        case UIEvent(name=name, data=data):
            return {"type": name, **data}
        case Error(message=message):
            return error(message, reply_id)
    raise ValueError(f"Unknown brain event: {ev!r}")
