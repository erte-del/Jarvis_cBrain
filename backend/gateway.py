"""OmniRoute (the optional gateway brain): is it running, start it, explain its errors.

Jarvis only ever runs one fixed command here: `omniroute serve --daemon`, and always
with OMNIROUTE_SERVER_HOST=127.0.0.1. OmniRoute's own default listens on every network
with no key, so anyone on the same Wi-Fi could use it (and your providers).
"""

import logging
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import config

log = logging.getLogger("jarvis.gateway")

START_WAIT_S = 40


def running() -> bool:
    """Does anything answer at the gateway's address? (Any HTTP reply counts.)"""
    try:
        urllib.request.urlopen(config.GATEWAY_URL, timeout=2).close()
    except urllib.error.HTTPError:
        pass  # it answered, just not with 200
    except (urllib.error.URLError, OSError):
        return False
    return True


def _is_local() -> bool:
    host = urllib.parse.urlparse(config.GATEWAY_URL).hostname or ""
    return host in ("localhost", "127.0.0.1", "::1")


def _find_omniroute() -> str | None:
    """The omniroute command. Jarvis.app starts without your shell's PATH, so also
    look where nvm installs global npm packages."""
    found = shutil.which("omniroute")
    if found:
        return found
    candidates = sorted(Path.home().glob(".nvm/versions/node/*/bin/omniroute"))
    return str(candidates[-1]) if candidates else None


def start() -> str | None:
    """Start OmniRoute in the background (on this Mac only). Returns None when it's up,
    else why not."""
    if not _is_local():
        return f"OmniRoute at {config.GATEWAY_URL} isn't reachable (Jarvis only starts a local one)."
    exe = _find_omniroute()
    if not exe:
        return "OmniRoute isn't installed. Install it with: npm i -g omniroute"
    port = str(urllib.parse.urlparse(config.GATEWAY_URL).port or 20128)
    # Its own environment: no Anthropic settings, and node on the PATH.
    env = {k: v for k, v in os.environ.items() if not k.startswith("ANTHROPIC_")}
    env["PATH"] = f"{Path(exe).parent}{os.pathsep}{env.get('PATH', '')}"
    env["OMNIROUTE_SERVER_HOST"] = "127.0.0.1"
    log.info("Starting OmniRoute on 127.0.0.1:%s", port)
    subprocess.Popen(
        [exe, "serve", "--daemon", "--no-open", "--no-tray", "--port", port],
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.monotonic() + START_WAIT_S
    while time.monotonic() < deadline:
        if running():
            return None
        time.sleep(1)
    return "OmniRoute didn't start. Try running it yourself: omniroute serve"


def explain_error(message: str) -> str:
    """OmniRoute's errors list every provider it tried. Say what to do about it."""
    return (
        f"{message}\n\nOmniRoute couldn't get an answer from any provider. Open {config.GATEWAY_URL}, "
        "add a provider under Providers (e.g. a free Gemini, Groq or OpenRouter API key), then try again. "
        "Or switch back to Claude with the gear icon."
    )
