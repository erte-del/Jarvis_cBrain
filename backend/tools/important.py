"""mark_important / unmark_important: files and folders Jarvis must ask about before changing.

Most actions run without a card now; the ones that still ask are those that reach other
people, and anything touching what's on this list (registry.needs_ok). Entries are note
paths ('School/Chemistry') or file and folder names ('Coursework'), in
storage/important.json. Adding one only adds protection, so it runs freely; removing one
asks first, so nothing can quietly lift the protection and then change the file.
"""

import json
from typing import Any

from claude_agent_sdk import tool

from config import STORAGE_DIR

IMPORTANT_FILE = STORAGE_DIR / "important.json"


def normalize(text: str) -> str:
    """'/School/Chemistry.md ' -> 'school/chemistry'."""
    text = text.strip().strip("/").lower()
    return text.removesuffix(".md")


def entries() -> list[str]:
    try:
        return json.loads(IMPORTANT_FILE.read_text())
    except (OSError, ValueError):
        return []


def _save(items: list[str]) -> None:
    IMPORTANT_FILE.write_text(json.dumps(sorted(set(items)), ensure_ascii=False, indent=1))


def matches(text: str) -> bool:
    """True if the text names an important entry or something inside one."""
    text = normalize(text)
    return any(text == e or text.startswith(e + "/") for e in entries())


def _text(text: str, is_error: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["is_error"] = True
    return result


def _listing() -> str:
    return "Important: " + ", ".join(entries()) if entries() else "Nothing is marked important."


@tool(
    "mark_important",
    "Mark a file or folder as important when the user says so: Jarvis then asks them before "
    "changing, moving or deleting it or anything inside it. path: a notes path ('School/Chemistry') "
    "or a file or folder name, e.g. in Google Drive ('Coursework'). Leave it empty to list them.",
    {"type": "object", "properties": {"path": {"type": "string"}}},
)
async def mark_important(args: dict[str, Any]) -> dict[str, Any]:
    path = normalize(str(args.get("path") or ""))
    if path:
        _save([*entries(), path])
    return _text(_listing())


@tool(
    "unmark_important",
    "Stop treating a file or folder as important (the user approves it on a card).",
    {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
async def unmark_important(args: dict[str, Any]) -> dict[str, Any]:
    path = normalize(str(args.get("path") or ""))
    if path not in entries():
        return _text(f"{path!r} isn't marked important. {_listing()}", True)
    _save([e for e in entries() if e != path])
    return _text(_listing())
