# Comfydark.app (native WKWebView wrapper)

A 200-line native macOS app that wraps the local opencode proxy
(`http://127.0.0.1:1234/` by default) in a WKWebView. Built so:

- The bundle identifier is **stable and chosen by you** (default
  `dev.jens.comfydark.opencode`) — aerospace / window-manager rules that
  match on `app-id` keep working across reinstalls and across machines.
- The app uses **system WebKit**, not bundled Chromium, so the binary is a
  few hundred KB and starts instantly.
- No Xcode project, no Swift Package Manager — just `main.swift` +
  `Info.plist` + `build.sh`.

## Requirements

- macOS 11.0+
- Xcode Command Line Tools (`xcode-select --install`) — for `swiftc`.
- The `opencode-proxy` LaunchAgent from the parent folder running on port
  1234 (or set `COMFYDARK_URL` to point elsewhere).

## Build & install

```sh
./build.sh --install
```

This compiles, ad-hoc-signs, and copies `Comfydark.app` to `~/Applications`.
Launch with Spotlight, `open ~/Applications/Comfydark.app`, or the Dock.

Without `--install`, the app lands in `./dist/Comfydark.app` and you launch
it from there.

### Configuration via env vars

| Var | Default | Effect |
|---|---|---|
| `APP_NAME` | `Comfydark` | Binary + .app name. |
| `BUNDLE_ID` | `dev.jens.comfydark.opencode` | Baked into `Info.plist`. **Change to make it yours.** |
| `INSTALL_DIR` | `~/Applications` | Where `--install` copies the bundle. |
| `COMFYDARK_URL` (runtime, not build) | `http://127.0.0.1:1234/` | URL the app loads on launch. |

Build with a different bundle ID:

```sh
BUNDLE_ID=me.example.opencode ./build.sh --install
```

Run pointing at a different URL:

```sh
COMFYDARK_URL=http://192.168.1.42:1234/ open ~/Applications/Comfydark.app
```

## Keybindings

| Key | Action |
|---|---|
| `⌘R` | Reload from origin |
| `⌘⇧H` | Go to home URL |
| `⌘[` / `⌘]` | Back / Forward |
| `⌃⌘F` | Toggle full screen |
| `⌥⌘I` | Toggle Web Inspector (devtools) |
| `⌘Q` | Quit |

## Aerospace example

Add to `~/.config/aerospace/aerospace.toml`:

```toml
[[on-window-detected]]
if.app-id = 'dev.jens.comfydark.opencode'
run = ['layout tiles', 'move-node-to-workspace 4']
```

Replace `dev.jens.comfydark.opencode` with whatever `BUNDLE_ID` you built
with.

## Caveats

- **First launch may need a Gatekeeper poke.** The build script uses ad-hoc
  signing. If macOS refuses to open the app, run:
  `xattr -dr com.apple.quarantine ~/Applications/Comfydark.app`
- **No app icon yet.** Drop a `.icns` file into the build script later
  (`cp icon.icns "$APP/Contents/Resources/AppIcon.icns"` plus a
  `CFBundleIconFile` key in `Info.plist`) if you want a custom one.
- **One window only.** Closing it quits the app
  (`applicationShouldTerminateAfterLastWindowClosed → true`). Adjust in
  `main.swift` if you want it to persist.
