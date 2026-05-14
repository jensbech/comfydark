#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
THEME_FILE="$SCRIPT_DIR/comfydark.json"
PROXY_FILE="$SCRIPT_DIR/proxy.ts"

: "${PORT:=1234}"
: "${LISTEN_HOST:=0.0.0.0}"
: "${UPSTREAM_HOST:=127.0.0.1}"
: "${UPSTREAM_PORT:=4096}"
: "${OVERRIDE_ID:=amoled}"

BUN_PATH="$(command -v bun || true)"
if [[ -z "$BUN_PATH" ]]; then
  echo "ERROR: bun is required but not on PATH." >&2
  echo "Install with:   curl -fsSL https://bun.sh/install | bash" >&2
  echo "          or:   brew install oven-sh/bun/bun" >&2
  exit 1
fi

if ! curl -fsS -o /dev/null --max-time 2 "http://${UPSTREAM_HOST}:${UPSTREAM_PORT}/doc"; then
  echo "WARNING: opencode upstream not reachable at http://${UPSTREAM_HOST}:${UPSTREAM_PORT}/." >&2
  echo "         Proxy will install and run, but won't serve until opencode is up." >&2
fi

LABEL="opencode-proxy"
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
		<string>${BUN_PATH}</string>
		<string>${PROXY_FILE}</string>
	</array>
	<key>EnvironmentVariables</key>
	<dict>
		<key>PATH</key>
		<string>$(dirname "$BUN_PATH"):/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
		<key>HOME</key>
		<string>${HOME}</string>
		<key>PORT</key>
		<string>${PORT}</string>
		<key>HOSTNAME</key>
		<string>${LISTEN_HOST}</string>
		<key>UPSTREAM_HOST</key>
		<string>${UPSTREAM_HOST}</string>
		<key>UPSTREAM_PORT</key>
		<string>${UPSTREAM_PORT}</string>
		<key>OVERRIDE_ID</key>
		<string>${OVERRIDE_ID}</string>
		<key>THEME_FILE</key>
		<string>${THEME_FILE}</string>
	</dict>
	<key>WorkingDirectory</key>
	<string>${SCRIPT_DIR}</string>
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
  echo "  Listens:  http://${LISTEN_HOST}:${PORT}/  (forwarding to http://${UPSTREAM_HOST}:${UPSTREAM_PORT})"
  echo "  Logs:     ${LOG_DIR}/${LABEL}.{out,err}.log"
  echo "  Theme:    ${THEME_FILE}"
  echo
  echo "Open http://127.0.0.1:${PORT}/ and pick the '${OVERRIDE_ID}' theme in the picker."
else
  echo "Install wrote plist but the agent isn't running. Check ${LOG_DIR}/${LABEL}.err.log" >&2
  exit 1
fi
