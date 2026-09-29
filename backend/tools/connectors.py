"""claude.ai connectors (Gmail, Supabase, Canva, ...): read/act labels.

Claude Code signed in with the Pro account brings in every connector enabled on
claude.ai. Their tools are named like `mcp__claude_ai_Gmail__search_threads`.
There are hundreds and connectors add new ones, so instead of listing them we
label them by their action verb:

  read — the action starts with a read verb (get_, list_, search_, ...) -> runs freely
  act  — anything else (send, reply, create, delete, trash, execute, ...) -> asks you first

Unknown verbs are 'act': when in doubt, Jarvis asks.
"""

import json
import re
from typing import Any, Iterator

CONNECTOR_PREFIX = "mcp__claude_ai_"

READ_VERBS = {"get", "list", "search", "read", "fetch", "find", "resolve", "describe", "view", "help"}

# Read-only tools whose name doesn't start with a read verb, per connector.
READ_EXTRA: dict[str, set[str]] = {
    "Claude_Docs": {"query", "guide"},
    "Supabase": {"query_logs"},
    "Google_Calendar": {"suggest_time"},
    "TickTick": {"filter_tasks"},
}


def parse(name: str) -> tuple[str, str] | None:
    """'mcp__claude_ai_Gmail__search_threads' -> ('Gmail', 'search_threads'). None if not a connector."""
    if not name.startswith(CONNECTOR_PREFIX):
        return None
    connector, sep, action = name.removeprefix(CONNECTOR_PREFIX).partition("__")
    return (connector, action) if sep and action else None


def is_read(name: str) -> bool:
    parsed = parse(name)
    if parsed is None:
        return False
    connector, action = parsed
    verb = re.split(r"[_\-]", action.lower(), maxsplit=1)[0]
    return verb in READ_VERBS or action in READ_EXTRA.get(connector, set())


# Calendar events and tasks Jarvis has seen in tool results, so a confirmation card
# that only gets an id (eventId, task_id) can still say which one it is.
REMEMBER_FROM = {"Google_Calendar", "TickTick"}
_seen: dict[str, str] = {}


def remember_items(name: str, result: Any) -> None:
    parsed = parse(name)
    if parsed is None or parsed[0] not in REMEMBER_FROM:
        return
    for obj in _dicts(result):
        label = obj.get("summary") or obj.get("title")
        if obj.get("id") and label:
            when = obj.get("start") or obj.get("dueDate")
            if isinstance(when, dict):
                when = when.get("dateTime") or when.get("date")
            _seen[str(obj["id"])] = f"{label} ({when})" if when else str(label)


def item_label(item_id: str) -> str | None:
    """'h5hdgf82...' -> 'Jarvis test (2026-09-30T16:00:00+04:00)', if Jarvis has seen it."""
    return _seen.get(item_id)


def _dicts(value: Any) -> Iterator[dict]:
    """Every dict inside a tool result; JSON text is parsed on the way."""
    if isinstance(value, str) and value[:1] in "{[":
        try:
            value = json.loads(value)
        except ValueError:
            return
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from _dicts(v)
    elif isinstance(value, list):
        for v in value:
            yield from _dicts(v)
