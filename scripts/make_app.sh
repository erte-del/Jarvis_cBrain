#!/bin/bash
# Build Jarvis.app in the project folder.
#   scripts/make_app.sh
# Run it again if you move the project folder (the app remembers where it is).
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/Jarvis.app"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

chmod +x "$ROOT/scripts/start_jarvis.sh" "$ROOT/scripts/stop_jarvis.sh"

# The app itself: a small AppleScript that stays open while Jarvis runs.
sed "s|__ROOT__|$ROOT|g" "$ROOT/scripts/Jarvis.applescript" >"$TMP/Jarvis.applescript"
rm -rf "$APP"
osacompile -s -o "$APP" "$TMP/Jarvis.applescript"

# Its icon: the blue orb. Remove the default icon (Assets.car), which macOS would
# otherwise prefer over applet.icns.
"$ROOT/backend/.venv/bin/python" "$ROOT/scripts/make_icon.py" "$TMP/Jarvis.iconset"
iconutil -c icns "$TMP/Jarvis.iconset" -o "$APP/Contents/Resources/applet.icns"
rm -f "$APP/Contents/Resources/Assets.car"
plutil -remove CFBundleIconName "$APP/Contents/Info.plist" 2>/dev/null || true

# Changing the app after osacompile signed it breaks the signature, and macOS
# won't open an app with a broken one. Sign it again (locally, "ad hoc").
codesign --force --sign - "$APP"
codesign --verify "$APP"
touch "$APP"  # tells Finder to pick up the new icon

echo "Built $APP"
