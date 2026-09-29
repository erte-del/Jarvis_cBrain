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
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
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

# Which brain Jarvis runs on. You can switch in the UI (gear icon); this is the choice
# at startup.
#   claude    - Claude on your Pro login (the default)
#   omniroute - OmniRoute (npm i -g omniroute), a gateway to other providers' models.
#               Doesn't use your Pro limit. The claude.ai connectors (Gmail, ...) stay
#               off, so your emails never go to those providers.
PROVIDERS = ("claude", "omniroute")
PROVIDER = os.getenv("JARVIS_PROVIDER", "claude").strip().lower()
if PROVIDER not in PROVIDERS:
    raise SystemExit(f"JARVIS_PROVIDER={PROVIDER!r}: use {' or '.join(PROVIDERS)}")

GATEWAY_URL = (os.getenv("JARVIS_GATEWAY_URL") or "http://localhost:20128").strip().rstrip("/")
GATEWAY_KEY = os.getenv("JARVIS_GATEWAY_KEY", "").strip()
if not GATEWAY_URL.startswith(("http://", "https://")):
    raise SystemExit(f"JARVIS_GATEWAY_URL={GATEWAY_URL!r}: must start with http:// or https://")
# Gateway models you can switch between in the app, as OmniRoute names them
# ("provider/model"). The first is the default. Each needs its provider connected in
# OmniRoute's dashboard.
GATEWAY_MODELS = [
    m.strip()
    for m in os.getenv("JARVIS_GATEWAY_MODELS", "gemini/gemini-3.1-flash-lite, gemini/gemini-3.8-flash, groq/openai/gpt-oss-120b").split(",")
    if m.strip()
]
if not GATEWAY_MODELS:
    raise SystemExit("JARVIS_GATEWAY_MODELS is empty: list at least one OmniRoute model")
# Claude Code's own sonnet / opus / haiku names (e.g. for WebFetch) go to this one.
GATEWAY_MODEL = GATEWAY_MODELS[0]

# If any of these are set, Claude Code uses them instead of the Pro login.
_API_AUTH_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL")
# Where Claude Code's model names go. Your own values (from .env) are kept for the
# gateway only: on the Pro login they would ask Claude for a model it doesn't have.
_MODEL_VARS = ("ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL")
_GATEWAY_MODELS = {var: os.environ.pop(var) for var in _MODEL_VARS if os.environ.get(var)}

log = logging.getLogger("jarvis.config")
_gateway_env_set = False  # True while the variables below were put there by Jarvis


def set_login(provider: str = "claude") -> None:
    """Point Claude Code at the Pro login (provider "claude") or at the gateway.

    The Claude Code subprocesses (Jarvis and ask_expert) inherit this process's
    environment when they start, so setting it here is enough.
    """
    global _gateway_env_set
    for var in (*_API_AUTH_VARS, *_MODEL_VARS):
        removed = os.environ.pop(var, None) is not None
        if removed and not _gateway_env_set and var in _API_AUTH_VARS:
            log.warning("Removed %s from the environment (Jarvis uses the Pro login).", var)
    _gateway_env_set = provider == "omniroute"
    if _gateway_env_set:
        os.environ["ANTHROPIC_BASE_URL"] = GATEWAY_URL
        # Always set a token: without one Claude Code would send the Pro login's token
        # to the gateway. Placeholder for gateways that don't check keys.
        os.environ["ANTHROPIC_AUTH_TOKEN"] = GATEWAY_KEY or "jarvis-gateway"
        for var in _MODEL_VARS:
            os.environ[var] = _GATEWAY_MODELS.get(var, GATEWAY_MODEL)
