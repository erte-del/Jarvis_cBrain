"""claude.ai connectors (Gmail, Supabase, Canva, ...): read/act labels.

Claude Code signed in with the Pro account brings in every connector enabled on
claude.ai. Their tools are named like `mcp__claude_ai_Gmail__search_threads`.
There are hundreds and connectors add new ones, so instead of listing them we
label them by their action verb:

  read — the action starts with a read verb (get_, list_, search_, ...) -> runs freely
  act  — anything else (send, reply, create, delete, trash, execute, ...) -> asks you first

Unknown verbs are 'act': when in doubt, Jarvis asks.
"""

import re

CONNECTOR_PREFIX = "mcp__claude_ai_"

READ_VERBS = {"get", "list", "search", "read", "fetch", "find", "resolve", "describe", "view", "help"}

# Read-only tools whose name doesn't start with a read verb, per connector.
READ_EXTRA: dict[str, set[str]] = {
    "Claude_Docs": {"query", "guide"},
    "Supabase": {"query_logs"},
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
