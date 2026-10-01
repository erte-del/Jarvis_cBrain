#!/bin/bash
# Start Jarvis (if it isn't running yet) and open it in the browser.
# Used by Jarvis.app; you can also run it yourself: scripts/start_jarvis.sh
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
URL="http://127.0.0.1:8000"
LOG="$ROOT/backend/storage/jarvis.log"
PIDFILE="$ROOT/backend/storage/jarvis.pid"

AGENT="gui/$(id -u)/com.jarvis.backend"  # scripts/autostart.sh

running() { curl -s -m 1 "$URL/health" >/dev/null 2>&1; }

# Rebuild the page if its code changed since the last build. Also when Jarvis is
# already running (autostart): he serves the new files without a restart.
DIST="$ROOT/frontend/dist/index.html"
CHANGED="$(find "$ROOT/frontend/src" "$ROOT/frontend/index.html" "$ROOT/frontend/vite.config.ts" \
  -newer "$DIST" -print -quit 2>/dev/null)"
if [ ! -f "$DIST" ] || [ -n "$CHANGED" ]; then
  # Node comes from nvm, which apps don't load: find it ourselves.
  NODE_BIN="$(ls -d "$HOME"/.nvm/versions/node/*/bin 2>/dev/null | sort -V | tail -1)"
  echo "building the page with node from ${NODE_BIN:-PATH}" >>"$LOG"
  if ! PATH="$NODE_BIN:/opt/homebrew/bin:/usr/local/bin:$PATH" \
    npm --prefix "$ROOT/frontend" run build >>"$LOG" 2>&1; then
    echo "Building the page failed. Details: $LOG" >&2
    exit 1
  fi
fi

if ! running; then
  echo "=== $(date) starting Jarvis" >>"$LOG"

  if launchctl print "$AGENT" >/dev/null 2>&1; then
    launchctl kickstart "$AGENT"  # autostart is on: launchd runs him, don't start a second one
    LOG="$HOME/Library/Logs/Jarvis.log"
  else
    cd "$ROOT/backend" || exit 1
    nohup .venv/bin/python main.py </dev/null >>"$LOG" 2>&1 &
    echo $! >"$PIDFILE"
  fi

  for _ in $(seq 1 60); do  # up to 30 seconds
    running && break
    sleep 0.5
  done
  if ! running; then
    echo "Jarvis didn't start. Details: $LOG" >&2
    exit 1
  fi
fi

open "$URL"
