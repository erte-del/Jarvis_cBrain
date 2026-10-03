#!/bin/bash
# One-time setup so Ultron can tell where this Mac is (mac_read what=location).
#   scripts/setup_location.sh
# Builds backend/storage/UltronLocation.app from scripts/locate.swift (needs the Xcode
# command line tools: xcode-select --install), then runs it once so macOS asks you to
# allow Location. It's only rebuilt when locate.swift changed: a rebuilt app is a new app
# to macOS, so you have to allow it again (System Settings → Location Services).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/backend/storage/UltronLocation.app"
BIN="$APP/Contents/MacOS/UltronLocation"

if [ -x "$BIN" ] && [ "$BIN" -nt "$ROOT/scripts/locate.swift" ] && [ "$BIN" -nt "$0" ]; then
  echo "== UltronLocation.app is up to date (not rebuilt, so macOS keeps its permission)."
else
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
swiftc -O "$ROOT/scripts/locate.swift" -o "$APP/Contents/MacOS/UltronLocation"
cat >"$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleIdentifier</key><string>local.ultron.location</string>
	<key>CFBundleName</key><string>Ultron Location</string>
	<key>CFBundleExecutable</key><string>UltronLocation</string>
	<key>CFBundlePackageType</key><string>APPL</string>
	<key>CFBundleVersion</key><string>1</string>
	<key>LSUIElement</key><true/>
	<key>NSLocationUsageDescription</key><string>Ultron uses your location for weather, directions and things nearby.</string>
	<key>NSLocationWhenInUseUsageDescription</key><string>Ultron uses your location for weather, directions and things nearby.</string>
</dict>
</plist>
EOF
codesign --force --sign - "$APP"
fi

echo "== Asking macOS for Location (click Allow if it asks)…"
OUT="$(mktemp)"
open -W -n --stdout "$OUT" "$APP"
cat "$OUT"; echo
rm -f "$OUT"
echo "== If it says denied: System Settings → Privacy & Security → Location Services → Ultron Location on."
