"""Settings loaded from .env."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
STORAGE_DIR = BACKEND_DIR / "storage"

load_dotenv(ROOT_DIR / ".env")

HOST = os.getenv("JARVIS_HOST", "127.0.0.1")
PORT = int(os.getenv("JARVIS_PORT", "8000"))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
BLENDER_PATH = os.getenv("BLENDER_PATH", "/Applications/Blender.app/Contents/MacOS/Blender")

# How hard Claude thinks before answering: low | medium | high | xhigh | max.
# Thinking was the biggest single use of the Pro limit, so the default is medium.
EFFORT = os.getenv("JARVIS_EFFORT", "medium").strip().lower()
if EFFORT not in ("low", "medium", "high", "xhigh", "max"):
    raise SystemExit(f"JARVIS_EFFORT={EFFORT!r}: use low, medium, high, xhigh or max")

# Which claude.ai connectors Jarvis loads: "all", or names like "Gmail, Canva".
# Each connector's tool list goes into every new conversation, so fewer = cheaper.
CONNECTORS = [c.strip().lower() for c in os.getenv("JARVIS_CONNECTORS", "all").split(",") if c.strip()]

# After this many minutes without a message, a big conversation starts over fresh.
# Claude's copy of the conversation (the cache) expires after an hour, so the next
# message would otherwise send the whole thing again at full price. 0 = never.
NEW_CHAT_AFTER_IDLE_MIN = int(os.getenv("JARVIS_NEW_CHAT_AFTER_IDLE_MIN", "60"))

if HOST not in ("127.0.0.1", "localhost", "::1"):
    raise SystemExit(f"JARVIS_HOST={HOST!r} refused: Jarvis only listens on this machine.")

# If any of these are set, Claude Code uses them instead of the Pro login.
_API_AUTH_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL")

log = logging.getLogger("jarvis.config")


def use_pro_login() -> None:
    """Remove API credentials from this process so Claude Code falls back to the Pro login.

    The Claude Code subprocess inherits this process's environment, so
    clearing them here is enough.
    """
    for var in _API_AUTH_VARS:
        if os.environ.pop(var, None) is not None:
            log.warning("Removed %s from the environment (Jarvis uses the Pro login).", var)
