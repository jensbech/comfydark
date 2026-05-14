# ComfyDark for opencode (desktop / PWA)

The `opencode serve` command exposes a built-in web UI with a fixed set of
themes baked into its JS bundle — there is no documented way to load a custom
theme on the desktop / PWA side. This folder adds Comfydark anyway, by running
a small reverse proxy in front of opencode that intercepts one built-in
theme chunk URL and returns Comfydark instead.

The cost: one theme slot is "consumed" (default: AMOLED). The slot's label in
the picker still reads its original name (e.g. `AMOLED`) because the label map
is hard-coded in the main bundle; only the colors change.

## Layout

| File | Purpose |
|---|---|
| `comfydark.json` | Theme palette + override map, in opencode's `desktop-theme.json` schema. Edit this to retune colors. |
| `proxy.ts` | Bun reverse proxy. Forwards everything to the upstream opencode server except `/assets/<override-id>-*.js`, which is replaced with `comfydark.json` wrapped as an ES module. |
| `install.sh` | Writes a launchd LaunchAgent at `~/Library/LaunchAgents/opencode-proxy.plist` and starts it. The agent auto-starts on login and respawns on crash. |
| `uninstall.sh` | Unloads and removes the LaunchAgent. |

## Requirements

- **macOS** (the installer uses `launchd`).
- **[Bun](https://bun.sh)** on `$PATH` — the proxy runs as a single Bun process.
- A running upstream `opencode serve` instance (default `127.0.0.1:4096`).

If you don't already have opencode running as a service, the simplest version
is a separate LaunchAgent that runs `opencode serve --hostname 127.0.0.1 --port 4096`.
The proxy doesn't manage that — keep them independent.

## Install

```sh
./install.sh
```

That:

1. Verifies Bun is available.
2. Pings the upstream opencode server (warns if unreachable but still installs).
3. Writes `~/Library/LaunchAgents/opencode-proxy.plist` with absolute paths to
   `bun`, `proxy.ts`, and `comfydark.json` in this folder.
4. Loads the agent (`launchctl load -w`). It starts immediately and on every
   subsequent login.

After install, open `http://127.0.0.1:1234/` and pick the **AMOLED** entry in
the theme picker — that slot is now ComfyDark.

### Configuration

The installer reads these environment variables (all optional):

| Var | Default | Meaning |
|---|---|---|
| `PORT` | `1234` | Port the proxy listens on. This is the URL you point your browser / PWA at. |
| `LISTEN_HOST` | `0.0.0.0` | `0.0.0.0` = reachable from other devices on your LAN; `127.0.0.1` = local only. |
| `UPSTREAM_HOST` | `127.0.0.1` | Where the real opencode server is running. |
| `UPSTREAM_PORT` | `4096` | Same. |
| `OVERRIDE_ID` | `amoled` | Which built-in theme slot to replace. Any of `amoled`, `aura`, `ayu`, `dracula`, `nord`, `tokyonight`, etc. |

Example:

```sh
PORT=8080 UPSTREAM_PORT=5000 OVERRIDE_ID=dracula ./install.sh
```

Re-running `./install.sh` reinstalls cleanly — it unloads any existing agent
with the same label before writing the new plist.

## Editing the theme

Edit `comfydark.json`, then either:

- Soft refresh: reload the page in the browser. The proxy reads
  `comfydark.json` from disk on every request, so changes pick up instantly.
- Or force the running agent to restart:
  `launchctl kickstart -k gui/$(id -u)/opencode-proxy`

You may also need to switch to a different theme in the picker and back
(opencode caches computed CSS in `localStorage` under
`opencode-theme-css-dark` / `…-light`).

## Uninstall

```sh
./uninstall.sh
```

Removes the plist and stops the agent. Nothing else to clean up — this folder
is the only state.

## How it works (notes for future tinkering)

opencode's web UI ships ~40 themes as code-split chunks under
`/assets/<theme-id>-<hash>.js`. Each chunk is a tiny ES module exporting
`{ $schema, name, id, light, dark }` where `light`/`dark` are
`{ palette, overrides }` pairs. The bundle imports the chunk by id and feeds
the variant into a derivation function that builds the full `--syntax-*`,
`--background-*`, `--text-*`, etc. CSS variable map; user-supplied `overrides`
are merged on top of the derived values.

The proxy regex-matches `/assets/<OVERRIDE_ID>-*.js` and serves
`export default <comfydark.json>;` at that URL. The hash portion is ignored,
so upgrades that change the chunk's content hash still work — only the
filename pattern would have to change for it to break.

Logs: `~/Library/Logs/opencode-proxy.{out,err}.log`.

## Caveats

- **Picker label** still says `AMOLED` (or whatever `OVERRIDE_ID` you picked).
  Fixable in principle by also rewriting the main bundle, but it would have
  to re-rewrite on every opencode upgrade as the bundle filename hashes
  change.
- **No auth.** The proxy passes requests through verbatim. If you want HTTP
  basic auth, set `OPENCODE_SERVER_PASSWORD` on the upstream opencode service
  and configure your client to send the `opencode:<password>` credential —
  the proxy doesn't interfere.
- **Light mode** is currently a copy of dark mode in `comfydark.json`.
  Replace the `light` block if you want different light-mode colors.
