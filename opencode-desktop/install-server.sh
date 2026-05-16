#!/usr/bin/env bash
set -euo pipefail

: "${UPSTREAM_HOST:=127.0.0.1}"
: "${UPSTREAM_PORT:=4096}"

OPENCODE_PATH="$(command -v opencode || true)"
if [[ -z "$OPENCODE_PATH" ]]; then
  echo "ERROR: opencode is required but not on PATH." >&2
  echo "Install from https://opencode.ai or:   brew install sst/tap/opencode" >&2
  exit 1
fi

LABEL="opencode-server"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="$HOME/Library/Logs"
mkdir -p "$LOG_DIR" "$(dirname "$PLIST")"

if launchctl list 2>/dev/null | awk '{print $3}' | grep -qx "${LABEL}"; then
  launchctl unload "$PLIST" 2>/dev/null || true
fi

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>${LABEL}</string>
	<key>ProgramArguments</key>
	<array>
		<string>${OPENCODE_PATH}</string>
		<string>serve</string>
		<string>--hostname</string>
		<string>${UPSTREAM_HOST}</string>
		<string>--port</string>
		<string>${UPSTREAM_PORT}</string>
	</array>
	<key>EnvironmentVariables</key>
	<dict>
		<key>PATH</key>
		<string>$(dirname "$OPENCODE_PATH"):/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
		<key>HOME</key>
		<string>${HOME}</string>
	</dict>
	<key>WorkingDirectory</key>
	<string>${HOME}</string>
	<key>RunAtLoad</key>
	<true/>
	<key>KeepAlive</key>
	<true/>
	<key>ThrottleInterval</key>
	<integer>10</integer>
	<key>StandardOutPath</key>
	<string>${LOG_DIR}/${LABEL}.out.log</string>
	<key>StandardErrorPath</key>
	<string>${LOG_DIR}/${LABEL}.err.log</string>
</dict>
</plist>
EOF

launchctl load -w "$PLIST"

sleep 1
if launchctl list 2>/dev/null | awk '{print $3}' | grep -qx "${LABEL}"; then
  echo "Installed and running."
  echo "  Plist:    $PLIST"
  echo "  Serves:   http://${UPSTREAM_HOST}:${UPSTREAM_PORT}/"
  echo "  Logs:     ${LOG_DIR}/${LABEL}.{out,err}.log"
  echo "  Binary:   ${OPENCODE_PATH}"
else
  echo "Install wrote plist but the agent isn't running. Check ${LOG_DIR}/${LABEL}.err.log" >&2
  exit 1
fi
