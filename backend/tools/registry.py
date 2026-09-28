"""All Jarvis tools + read/act labels, SDK MCP server.

Every tool is labelled:
  read — runs freely (searching, looking things up, thinking)
  act  — sends, deletes, buys or changes something; needs your confirmation (Phase 6)

To add a tool: write it with the SDK's @tool decorator, then add it to TOOLS.
"""

from dataclasses import dataclass
from typing import Any, Literal

from claude_agent_sdk import HookMatcher, SdkMcpTool, create_sdk_mcp_server

from . import web
from .expert import ask_expert

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
]

# Claude Code's own built-in tools that Jarvis may use (all 'read').
BUILTIN_READ_TOOLS: list[str] = [*web.WEB_TOOLS]


def builtin_tools() -> list[str]:
    return list(BUILTIN_READ_TOOLS)


def hooks() -> dict[str, list[HookMatcher]]:
    """Checks that run before a tool does."""
    return {"PreToolUse": [HookMatcher(matcher="WebFetch", hooks=[web.block_private_urls])]}


def mcp_servers() -> dict[str, Any]:
    """The in-process MCP server that exposes Jarvis's tools to Claude Code."""
    return {SERVER_NAME: create_sdk_mcp_server(SERVER_NAME, tools=[t.tool for t in TOOLS])}


def auto_allowed() -> list[str]:
    """Tools that run without asking: all 'read' tools."""
    return BUILTIN_READ_TOOLS + [t.full_name for t in TOOLS if t.kind == "read"]


def short_name(name: str) -> str:
    """'mcp__jarvis__ask_expert' -> 'ask_expert'. Other names are unchanged."""
    return name.removeprefix(PREFIX)
