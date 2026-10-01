#!/bin/bash
# One-time setup so Jarvis can tell where this Mac is (mac_read what=location).
#   scripts/setup_location.sh
# Builds backend/storage/JarvisLocation.app from scripts/locate.swift (needs the Xcode
# command line tools: xcode-select --install), then runs it once so macOS asks you to
# allow Location. Rebuilding makes macOS ask again.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/backend/storage/JarvisLocation.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
swiftc -O "$ROOT/scripts/locate.swift" -o "$APP/Contents/MacOS/JarvisLocation"
cat >"$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleIdentifier</key><string>local.jarvis.location</string>
	<key>CFBundleName</key><string>Jarvis Location</string>
	<key>CFBundleExecutable</key><string>JarvisLocation</string>
	<key>CFBundlePackageType</key><string>APPL</string>
	<key>CFBundleVersion</key><string>1</string>
	<key>LSUIElement</key><true/>
	<key>NSLocationUsageDescription</key><string>Jarvis uses your location for weather, directions and things nearby.</string>
	<key>NSLocationWhenInUseUsageDescription</key><string>Jarvis uses your location for weather, directions and things nearby.</string>
</dict>
</plist>
EOF
codesign --force --sign - "$APP"

echo "== Asking macOS for Location (click Allow)…"
OUT="$(mktemp)"
open -W -n --stdout "$OUT" "$APP"
cat "$OUT"; echo
rm -f "$OUT"
echo "== If it says denied: System Settings → Privacy & Security → Location Services → Jarvis Location on."
