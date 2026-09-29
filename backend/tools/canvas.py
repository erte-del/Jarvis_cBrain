"""show_on_canvas -> UI events. (Phase 4a)

The canvas is the panel next to the chat where Jarvis *shows* things. Cards are
pushed to every open tab through the hub. Later steps add images and 3D objects.
"""

import re
from typing import Any

from claude_agent_sdk import tool

import events
import hub

CARD_KINDS = ["text", "table", "email_list", "events"]

# Fields each list item may have, per kind (all strings; anything else is dropped).
ITEM_FIELDS = {
    "email_list": ["from", "subject", "date", "snippet", "unread", "id"],
    "events": ["title", "start", "end", "location", "notes"],
}
MAX_ITEMS = 50

_last_card = 0


def _new_card_id() -> str:
    global _last_card
    _last_card += 1
    return f"card_{_last_card}"


def restored(card_ids: list[str]) -> None:
    """Cards of a loaded chat are back on the canvas: new cards mustn't reuse their ids
    (the count starts at 1 again whenever the server restarts)."""
    global _last_card
    for card_id in card_ids:
        if m := re.fullmatch(r"card_(\d+)", card_id):
            _last_card = max(_last_card, int(m[1]))

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {
            "type": "string",
            "enum": CARD_KINDS,
            "description": "text: markdown content. table: columns + rows. "
            "email_list: items with from/subject/date/snippet/unread. "
            "events: items with title/start/end/location/notes.",
        },
        "title": {"type": "string", "description": "Short card title."},
        "content": {"type": "string", "description": "For kind=text: the markdown to show."},
        "columns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "For kind=table: column headings.",
        },
        "rows": {
            "type": "array",
            "items": {"type": "array", "items": {"type": ["string", "number", "boolean", "null"]}},
            "description": "For kind=table: one array of cell values per row.",
        },
        "items": {
            "type": "array",
            "items": {"type": "object"},
            "description": "For kind=email_list or events: one object per email / event.",
        },
        "replace_card_id": {
            "type": "string",
            "description": "To update a card you showed earlier, pass its id (e.g. card_2).",
        },
    },
    "required": ["kind", "title"],
}


def _card_data(args: dict[str, Any]) -> dict[str, Any]:
    kind = args["kind"]
    if kind == "text":
        content = str(args.get("content") or "").strip()
        if not content:
            raise ValueError("kind=text needs 'content'")
        return {"content": content}
    if kind == "table":
        columns = [str(c) for c in args.get("columns") or []]
        rows = [["" if v is None else str(v) for v in row] for row in args.get("rows") or []]
        if not columns:
            raise ValueError("kind=table needs 'columns'")
        return {"columns": columns, "rows": rows}
    if kind in ITEM_FIELDS:
        fields = ITEM_FIELDS[kind]
        items = []
        for raw in (args.get("items") or [])[:MAX_ITEMS]:
            if isinstance(raw, dict):
                items.append({f: str(raw[f]) for f in fields if raw.get(f) not in (None, "")})
        if not items:
            raise ValueError(f"kind={kind} needs 'items'")
        return {"items": items}
    raise ValueError(f"Unknown card kind {kind!r}; use one of {CARD_KINDS}")


async def show_text(title: str, content: str) -> str:
    """Put a markdown card on the canvas from Jarvis's own code. Returns the card id."""
    card_id = _new_card_id()
    await hub.emit(events.canvas_card(card_id, "text", title, {"content": content}))
    return card_id


async def show_table(title: str, columns: list[str], rows: list[list[str]]) -> str:
    """Put a table card on the canvas from Jarvis's own code. Returns the card id."""
    card_id = _new_card_id()
    await hub.emit(events.canvas_card(card_id, "table", title, {"columns": columns, "rows": rows}))
    return card_id


@tool(
    "show_on_canvas",
    "Show content on the canvas, the panel next to the chat. Use it for things better "
    "seen than read in a chat bubble: tables and comparisons, structured data, longer "
    "documents, drafts, plans, code. Keep your chat reply short and refer to the card. "
    "Returns the card id, which you can pass as replace_card_id to update the card later.",
    INPUT_SCHEMA,
)
async def show_on_canvas(args: dict[str, Any]) -> dict[str, Any]:
    try:
        data = _card_data(args)
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Not shown: {e}"}], "is_error": True}

    card_id = args.get("replace_card_id") or _new_card_id()
    await hub.emit(events.canvas_card(card_id, args["kind"], str(args["title"]), data))
    note = "" if hub.has_clients() else " (no browser is open, so nobody can see it right now)"
    return {"content": [{"type": "text", "text": f"Shown on the canvas as {card_id}.{note}"}]}
