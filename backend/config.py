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
