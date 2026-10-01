#!/bin/bash
# Stop the Jarvis backend that start_jarvis.sh started (quitting Jarvis.app runs this).
# A backend you started yourself in a terminal is left alone.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDFILE="$ROOT/backend/storage/jarvis.pid"

# With autostart on (scripts/autostart.sh), launchd runs Jarvis and starts him again
# right after this: quitting Jarvis.app is then a restart.
launchctl kill TERM "gui/$(id -u)/com.jarvis.backend" 2>/dev/null && exit 0

[ -f "$PIDFILE" ] || exit 0
PID="$(cat "$PIDFILE")"
rm -f "$PIDFILE"

# Only stop it if that process is still our backend (process IDs get reused).
if ps -p "$PID" -o command= 2>/dev/null | grep -q "main.py"; then
  kill "$PID"
  for _ in $(seq 1 20); do  # let it shut down cleanly (up to 10 seconds)
    kill -0 "$PID" 2>/dev/null || exit 0
    sleep 0.5
  done
  kill -9 "$PID" 2>/dev/null
fi
exit 0
