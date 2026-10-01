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

# The app itself: a menu bar app (scripts/Jarvis.swift; needs the Xcode command line
# tools: xcode-select --install). LSUIElement keeps it out of the Dock.
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
swiftc -O "$ROOT/scripts/Jarvis.swift" -o "$APP/Contents/MacOS/Jarvis"
cat >"$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleIdentifier</key><string>local.jarvis.app</string>
	<key>CFBundleName</key><string>Jarvis</string>
	<key>CFBundleExecutable</key><string>Jarvis</string>
	<key>CFBundleIconFile</key><string>Jarvis</string>
	<key>CFBundlePackageType</key><string>APPL</string>
	<key>CFBundleVersion</key><string>1</string>
	<key>LSUIElement</key><true/>
</dict>
</plist>
EOF
plutil -insert JarvisRoot -string "$ROOT" "$APP/Contents/Info.plist"

# Its icon in Finder: the blue orb.
"$ROOT/backend/.venv/bin/python" "$ROOT/scripts/make_icon.py" "$TMP/Jarvis.iconset"
iconutil -c icns "$TMP/Jarvis.iconset" -o "$APP/Contents/Resources/Jarvis.icns"

# Sign it locally ("ad hoc"): macOS won't open an unsigned app on Apple silicon.
codesign --force --sign - "$APP"
codesign --verify "$APP"
touch "$APP"  # tells Finder to pick up the new icon

echo "Built $APP"
