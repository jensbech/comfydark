#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

: "${APP_NAME:=Comfydark}"
: "${BUNDLE_ID:=dev.jens.comfydark.opencode}"
: "${INSTALL_DIR:=$HOME/Applications}"

if ! command -v swiftc >/dev/null 2>&1; then
  echo "ERROR: swiftc not found. Install Xcode Command Line Tools:" >&2
  echo "  xcode-select --install" >&2
  exit 1
fi

DIST="$SCRIPT_DIR/dist"
APP="$DIST/$APP_NAME.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

sed "s|__BUNDLE_ID__|$BUNDLE_ID|g" Info.plist > "$APP/Contents/Info.plist"

if [[ -f icon.png ]]; then
  ICONSET="$DIST/AppIcon.iconset"
  rm -rf "$ICONSET" && mkdir -p "$ICONSET"
  SQUARE="$DIST/icon-square.png"
  sips -z 1024 1024 icon.png --out "$SQUARE" >/dev/null
  for sz in 16 32 64 128 256 512 1024; do
    sips -z $sz $sz "$SQUARE" --out "$ICONSET/icon_${sz}x${sz}.png" >/dev/null
  done
  mv "$ICONSET/icon_32x32.png"     "$ICONSET/icon_16x16@2x.png"
  cp "$ICONSET/icon_16x16@2x.png"  "$ICONSET/icon_32x32.png"
  mv "$ICONSET/icon_64x64.png"     "$ICONSET/icon_32x32@2x.png"
  mv "$ICONSET/icon_256x256.png"   "$ICONSET/icon_128x128@2x.png"
  cp "$ICONSET/icon_128x128@2x.png" "$ICONSET/icon_256x256.png"
  mv "$ICONSET/icon_1024x1024.png" "$ICONSET/icon_512x512@2x.png"
  cp "$ICONSET/icon_512x512@2x.png" "$ICONSET/icon_512x512.png"
  iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns"
  rm -rf "$ICONSET" "$SQUARE"
fi

swiftc -O \
    -framework Cocoa -framework WebKit \
    -o "$APP/Contents/MacOS/$APP_NAME" \
    main.swift

codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || true

echo "Built: $APP"
echo "Bundle ID: $BUNDLE_ID"

if [[ "${1:-}" == "--install" ]]; then
  mkdir -p "$INSTALL_DIR"
  rm -rf "$INSTALL_DIR/$APP_NAME.app"
  cp -R "$APP" "$INSTALL_DIR/"
  echo "Installed to: $INSTALL_DIR/$APP_NAME.app"
  echo "Launch:  open '$INSTALL_DIR/$APP_NAME.app'"
else
  echo
  echo "To install to ~/Applications:  ./build.sh --install"
  echo "To run from build dir:         open '$APP'"
fi
