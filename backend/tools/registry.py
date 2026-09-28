"""All Jarvis tools + read/act labels, SDK MCP server.

Every tool is labelled:
  read — runs freely (searching, looking things up, thinking)
  act  — sends, deletes, buys or changes something; needs your confirmation (Phase 6)

To add a tool: write it with the SDK's @tool decorator, then add it to TOOLS.
"""

from dataclasses import dataclass
from typing import Any, Literal

from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server

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


def mcp_servers() -> dict[str, Any]:
    """The in-process MCP server that exposes Jarvis's tools to Claude Code."""
    return {SERVER_NAME: create_sdk_mcp_server(SERVER_NAME, tools=[t.tool for t in TOOLS])}


def auto_allowed() -> list[str]:
    """Tools that run without asking: all 'read' tools."""
    return [t.full_name for t in TOOLS if t.kind == "read"]


def short_name(name: str) -> str:
    """'mcp__jarvis__ask_expert' -> 'ask_expert'. Other names are unchanged."""
    return name.removeprefix(PREFIX)
