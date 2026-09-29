"""Usage numbers for the panel on the right.

Two kinds:
  - Your Pro plan's windows (5 hours, 7 days): how much is used and when it resets.
    Claude Code reports these after each reply, as a fraction. Anthropic doesn't
    publish the limits as token counts, so "left" is a percentage too.
  - Jarvis's own tokens, per reply, kept in storage/usage.json so the 5-hour total
    survives a restart. (Tokens you use in Claude Code or on claude.ai aren't counted
    here, but they do count towards the plan windows above.)
"""

import json
import logging
import time
from typing import Any

from config import STORAGE_DIR

log = logging.getLogger("jarvis.usage")

FILE = STORAGE_DIR / "usage.json"
FIVE_HOURS = 5 * 3600
KEEP_S = 8 * 24 * 3600  # older turns are dropped

# Plan windows as last reported: {"five_hour": {"used": 0.16, "resets_at": 1790674800}, ...}
windows: dict[str, dict[str, float]] = {}
# One entry per reply: [time, model, input, cache_write, cache_read, output]
_turns: list[list[Any]] = []


def _load() -> None:
    try:
        data = json.loads(FILE.read_text())
        _turns.extend(t for t in data.get("turns", []) if isinstance(t, list) and len(t) == 6)
        windows.update(data.get("windows", {}))
    except FileNotFoundError:
        pass
    except Exception:
        log.warning("Could not read %s; starting fresh", FILE, exc_info=True)


def _save() -> None:
    cutoff = time.time() - KEEP_S
    _turns[:] = [t for t in _turns if t[0] > cutoff]
    try:
        FILE.write_text(json.dumps({"windows": windows, "turns": _turns}))
    except Exception:
        log.warning("Could not save %s", FILE, exc_info=True)


def record_limits(raw: dict[str, Any]) -> None:
    """From Claude Code's rate_limit_event."""
    for name, w in (raw.get("unifiedWindows") or {}).items():
        if isinstance(w, dict) and w.get("utilization") is not None:
            windows[name] = {"used": float(w["utilization"]), "resets_at": w.get("resetsAt") or 0}
    kind = raw.get("rateLimitType")
    if kind and raw.get("utilization") is not None:  # older CLIs: only the window that applies
        windows[kind] = {"used": float(raw["utilization"]), "resets_at": raw.get("resetsAt") or 0}
    _save()


def record_turn(model_usage: dict[str, Any] | None) -> None:
    """From a reply's ResultMessage.model_usage ({model: {inputTokens, ...}})."""
    now = time.time()
    for model, u in (model_usage or {}).items():
        _turns.append([
            now,
            model,
            int(u.get("inputTokens") or 0),
            int(u.get("cacheCreationInputTokens") or 0),
            int(u.get("cacheReadInputTokens") or 0),
            int(u.get("outputTokens") or 0),
        ])
    _save()


def snapshot(provider: str, context_tokens: int) -> dict[str, Any]:
    """Everything the usage panel shows."""
    now = time.time()
    five = windows.get("five_hour")
    # Jarvis's tokens since the current 5-hour window started (or the last 5 hours).
    if five and five["resets_at"] > now:
        since = five["resets_at"] - FIVE_HOURS
    else:
        since = now - FIVE_HOURS
    tokens = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    for t in _turns:
        if t[0] >= since:
            tokens["input"] += t[2]
            tokens["cache_write"] += t[3]
            tokens["cache_read"] += t[4]
            tokens["output"] += t[5]
    # A window that has reset since the last report is back to 0.
    current = {k: w if w["resets_at"] > now else {"used": 0.0, "resets_at": 0} for k, w in windows.items()}
    return {"provider": provider, "windows": current, "tokens": tokens, "context_tokens": context_tokens}


_load()
