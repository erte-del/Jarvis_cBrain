"""All Jarvis tools + read/act labels, SDK MCP server.

Every tool is labelled:
  read — runs freely (searching, looking things up, thinking)
  act  — sends, deletes, buys or changes something; needs your confirmation (Phase 4a)

To add a tool: write it with the SDK's @tool decorator, then add it to TOOLS.
claude.ai connector tools are labelled by their action verb (see connectors.py).
Any other tool Claude Code offers goes through the confirmation gate.
"""

import json
from contextlib import contextmanager

from dataclasses import dataclass
from typing import Any, Literal

import claude_agent_sdk
from claude_agent_sdk import HookMatcher, SdkMcpTool, create_sdk_mcp_server

from . import connectors, web
from .canvas import show_on_canvas
from .expert import ask_expert
from .images import image_edit, image_search, image_undo, image_versions
from .models3d import export_3d, get_3d_spec, preview_3d, revert_3d
from .spotify import spotify_control, spotify_playlist_tracks
from .uploads import read_upload
from .video import generate_video

SERVER_NAME = "jarvis"
PREFIX = f"mcp__{SERVER_NAME}__"  # how Claude Code names tools from this server


@dataclass(frozen=True)
class JarvisTool:
    tool: SdkMcpTool[Any]
    kind: Literal["read", "act"]

    @property
    def full_name(self) -> str:
        return PREFIX + self.tool.name


TOOLS: list[JarvisTool] = [
    JarvisTool(ask_expert, "read"),
    JarvisTool(show_on_canvas, "read"),
    # Image edits only change Jarvis's own copies and can always be undone.
    JarvisTool(image_search, "read"),
    JarvisTool(image_edit, "read"),
    JarvisTool(image_undo, "read"),
    JarvisTool(image_versions, "read"),
    # 3D previews only change Jarvis's own copies. The final file needs your approval.
    JarvisTool(preview_3d, "read"),
    JarvisTool(revert_3d, "read"),
    JarvisTool(get_3d_spec, "read"),
    JarvisTool(export_3d, "act"),
    # Playing music and reading your own playlists change nothing that matters.
    JarvisTool(spotify_control, "read"),
    JarvisTool(spotify_playlist_tracks, "read"),
    # Only reads files you uploaded yourself.
    JarvisTool(read_upload, "read"),
    # A video ties up the Mac for minutes, so it asks first.
    JarvisTool(generate_video, "act"),
]

# Friendlier titles for confirmation cards.
TITLES = {"export_3d": "Build the final 3D file", "generate_video": "Make a video (takes a few minutes)"}

# Claude Code's own built-in tools that Jarvis may use (all 'read').
# ToolSearch lets Claude find connector tools on demand instead of loading
# hundreds of tool descriptions into every message.
BUILTIN_READ_TOOLS: list[str] = [*web.WEB_TOOLS, "ToolSearch"]


def builtin_tools() -> list[str]:
    return list(BUILTIN_READ_TOOLS)


def classify(name: str) -> str:
    """'read' (runs freely) or 'act' (asks you first) for any tool name Claude Code uses."""
    if name in BUILTIN_READ_TOOLS:
        return "read"
    for t in TOOLS:
        if t.full_name == name:
            return t.kind
    if connectors.is_read(name):
        return "read"
    return "act"


def hooks() -> dict[str, list[HookMatcher]]:
    """Checks that run before a tool does."""
    return {"PreToolUse": [HookMatcher(matcher="WebFetch", hooks=[web.block_private_urls])]}


@contextmanager
def _always_load():
    """Mark Jarvis's own tools 'always load' so Tool Search doesn't hide them.

    Claude Code reads this from the tool's `_meta`; the SDK (0.2.x) only fills
    `_meta` from its own helper, so we wrap that helper while building our server.
    """
    original = claude_agent_sdk._build_meta

    def build_meta(tool_def):
        return {**(original(tool_def) or {}), "anthropic/alwaysLoad": True}

    claude_agent_sdk._build_meta = build_meta
    try:
        yield
    finally:
        claude_agent_sdk._build_meta = original


def mcp_servers() -> dict[str, Any]:
    """The in-process MCP server that exposes Jarvis's tools to Claude Code."""
    with _always_load():
        server = create_sdk_mcp_server(SERVER_NAME, tools=[t.tool for t in TOOLS])
    return {SERVER_NAME: server}


def auto_allowed() -> list[str]:
    """Tools that run without asking: all 'read' tools."""
    return BUILTIN_READ_TOOLS + [t.full_name for t in TOOLS if t.kind == "read"]


def short_name(name: str) -> str:
    """'mcp__jarvis__ask_expert' -> 'ask_expert'. Other names are unchanged."""
    return name.removeprefix(PREFIX)


def friendly_name(name: str) -> str:
    """A readable tool name for the confirmation card.

    'mcp__jarvis__save_note'             -> 'Save note'
    'mcp__claude_ai_Gmail__send_message'  -> 'Gmail: Send message'
    'mcp__claude_ai_Canva__search-designs' -> 'Canva: Search designs'
    """
    if name.startswith("mcp__"):
        server, _, tool_name = name.removeprefix("mcp__").partition("__")
        if server == SERVER_NAME and tool_name in TITLES:
            return TITLES[tool_name]
        action = tool_name.replace("_", " ").replace("-", " ").strip().capitalize() or tool_name
        if server == SERVER_NAME:
            return action
        service = server.removeprefix("claude_ai_").replace("_", " ").strip()
        return f"{service}: {action}"
    return name


MAX_DETAIL_CHARS = 600


def describe_call(name: str, tool_input: dict[str, Any]) -> tuple[str, str, list[list[str]]]:
    """(title, summary, details) describing a tool call, for the confirmation card."""
    title = friendly_name(name)
    summary = f"Jarvis wants to: {title}"
    details = []
    for key, value in tool_input.items():
        if isinstance(value, str):
            text = value
        elif isinstance(value, list) and all(isinstance(v, (str, int, float)) for v in value):
            text = ", ".join(str(v) for v in value)  # e.g. recipients
        else:
            text = json.dumps(value, ensure_ascii=False, indent=1)
        if len(text) > MAX_DETAIL_CHARS:
            text = text[:MAX_DETAIL_CHARS] + "…"
        details.append([key.replace("_", " "), text])
    return title, summary, details
