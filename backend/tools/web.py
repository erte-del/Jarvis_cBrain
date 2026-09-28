"""Web search: Claude Code's built-in WebSearch / WebFetch tools.

There is no search code to write; this module only
  - blocks WebFetch from reaching this machine or the local network, and
  - pulls source links out of tool results so the UI can show them as chips.
"""

import asyncio
import ipaddress
import logging
import re
import socket
from typing import Any
from urllib.parse import urlparse

log = logging.getLogger("jarvis.web")

WEB_TOOLS = ["WebSearch", "WebFetch"]

Source = dict[str, str]  # {"title": ..., "url": ...}


# ---- Safety: WebFetch may only reach the public internet --------------------------

_LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home", ".arpa")


def _is_public_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip.split("%")[0])
    return addr.is_global and not addr.is_multicast


async def is_public_url(url: str) -> tuple[bool, str]:
    """(ok, reason). Rejects localhost, private/LAN addresses and non-http(s) URLs.

    A web page could otherwise trick Jarvis into fetching http://127.0.0.1:... or
    your router's admin page.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "only http(s) URLs are allowed"
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host or host == "localhost" or host.endswith(_LOCAL_SUFFIXES) or "." not in host:
        return False, f"{host or 'empty host'} is a local address"
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return True, ""  # doesn't resolve; the fetch will just fail
    for info in infos:
        ip = info[4][0]
        if not _is_public_ip(ip):
            return False, f"{host} resolves to a private address ({ip})"
    return True, ""


async def block_private_urls(hook_input: dict[str, Any], tool_use_id: str | None, context: Any) -> dict:
    """PreToolUse hook for WebFetch."""
    url = hook_input.get("tool_input", {}).get("url", "")
    ok, reason = await is_public_url(url)
    if ok:
        return {}  # no opinion: normal permissions apply
    log.warning("Blocked WebFetch of %s: %s", url, reason)
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked: {reason}. Jarvis only fetches public web pages.",
        }
    }


# ---- Sources -----------------------------------------------------------------------

def tool_detail(name: str, tool_input: dict[str, Any]) -> str:
    """Short text for the UI while a web tool runs: the query, or the site being read."""
    if name == "WebSearch":
        return str(tool_input.get("query", ""))
    if name == "WebFetch":
        return domain(str(tool_input.get("url", "")))
    return ""


def sources_from_result(name: str, tool_input: dict[str, Any], data: Any) -> list[Source]:
    """Links a web tool looked at. `data` is Claude Code's structured tool result."""
    if not isinstance(data, dict):
        data = {}
    if name == "WebSearch":
        found = []
        for group in data.get("results") or []:
            if isinstance(group, dict):
                for item in group.get("content") or []:
                    if isinstance(item, dict) and item.get("url"):
                        found.append({"title": str(item.get("title") or ""), "url": str(item["url"])})
        return found
    if name == "WebFetch":
        url = data.get("url") or tool_input.get("url")
        return [{"title": "", "url": str(url)}] if url else []
    return []


_MD_LINK = re.compile(r"\[([^\]\n]+)\]\((https?://[^\s)]+)\)")
_BARE_URL = re.compile(r"(?<![(\[])\bhttps?://[^\s)>\]]+")


def links_in_text(text: str) -> list[Source]:
    """Markdown links and bare URLs in Claude's reply, in order."""
    found = [{"title": title, "url": url} for title, url in _MD_LINK.findall(text)]
    without_md = _MD_LINK.sub("", text)
    found += [{"title": "", "url": url.rstrip(".,;:")} for url in _BARE_URL.findall(without_md)]
    return found


def pick_sources(reply_text: str, looked_at: list[Source], fallback_count: int = 3) -> list[Source]:
    """Sources to show under the reply.

    Prefer the links Claude actually cited in its reply. If it cited none, show the
    pages it fetched plus the top few search results.
    """
    titles = {s["url"]: s["title"] for s in looked_at if s["title"]}
    cited = links_in_text(reply_text) if looked_at else []
    if cited:
        chosen = cited
    else:
        fetched = [s for s in looked_at if not s["title"]]
        searched = [s for s in looked_at if s["title"]][:fallback_count]
        chosen = fetched + searched

    result, seen = [], set()
    for s in chosen:
        if s["url"] in seen:
            continue
        seen.add(s["url"])
        result.append({"title": s["title"] or titles.get(s["url"], ""), "url": s["url"]})
    return result


def domain(url: str) -> str:
    host = urlparse(url).hostname or url
    return host.removeprefix("www.")
