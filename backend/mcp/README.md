# Connector configs (fallback path, Phase 4b)

MCP server configs for connectors (Gmail, Calendar, …) go here, used only if
the claude.ai connectors don't come through the Agent SDK.

Config files only. Don't add an `__init__.py` here: it would turn this folder
into a Python package called `mcp` that hides the real `mcp` library the
Agent SDK depends on.
