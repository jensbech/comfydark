#!/usr/bin/env bash
set -euo pipefail

LABEL="opencode-server"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"

if [[ -f "$PLIST" ]]; then
  launchctl unload "$PLIST" 2>/dev/null || true
  rm "$PLIST"
  echo "Removed ${PLIST} and stopped ${LABEL}."
else
  echo "No plist at ${PLIST}; nothing to do."
fi
