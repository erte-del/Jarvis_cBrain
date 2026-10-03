#!/bin/bash
# Start Ultron when you log in, and start him again if he crashes (a macOS LaunchAgent).
#   scripts/autostart.sh on     turn it on (run it again if you move the project folder)
#   scripts/autostart.sh off    turn it off and stop Ultron
# While it's on, quitting Ultron.app restarts Ultron instead of stopping him, and his
# log is ~/Library/Logs/Ultron.log (launchd can't write to a project in Desktop or Documents).
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.ultron.backend"  # also in start_ultron.sh and stop_ultron.sh
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
TARGET="gui/$(id -u)"
LOG="$HOME/Library/Logs/Ultron.log"

loaded() { launchctl print "$TARGET/$LABEL" >/dev/null 2>&1; }

case "${1:-}" in
on)
  if [ ! -f "$ROOT/frontend/dist/index.html" ]; then
    echo "Open Ultron.app once first: it builds the page." >&2
    exit 1
  fi
  ;;
off) ;;
*)
  echo "Usage: scripts/autostart.sh on|off" >&2
  exit 1
  ;;
esac

# Stop whatever is running now: the old agent, or a Ultron that Ultron.app started.
launchctl bootout "$TARGET/$LABEL" 2>/dev/null || true
for _ in $(seq 1 40); do  # bootout returns before he has shut down (up to 20 seconds)
  loaded || break
  sleep 0.5
done
"$ROOT/scripts/stop_ultron.sh"

if [ "$1" = off ]; then
  rm -f "$PLIST"
  echo "Autostart is off, and Ultron is stopped."
  exit 0
fi

mkdir -p "$(dirname "$PLIST")"
cat >"$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <!-- Through a shell: launchd itself may not open a project in Desktop or Documents. -->
    <string>/bin/bash</string>
    <string>-c</string>
    <string>cd "$ROOT/backend" &amp;&amp; exec .venv/bin/python main.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
EOF
launchctl bootstrap "$TARGET" "$PLIST"

for _ in $(seq 1 60); do  # up to 30 seconds
  if curl -s -m 1 "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
    echo "Autostart is on, and Ultron is running."
    exit 0
  fi
  sleep 0.5
done
echo "Autostart is on, but Ultron didn't start. Details: $LOG" >&2
exit 1
