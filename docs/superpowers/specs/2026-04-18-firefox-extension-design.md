# ComfyDark Firefox Extension — Design

## Goal

Ship a Firefox WebExtension, housed alongside the other per-app ports in this repo, that applies the ComfyDark palette to `github.com`. The target experience is that reading and reviewing code on GitHub — especially diffs — looks like the ComfyDark VS Code theme.

## Scope

In scope:

- `github.com` only (no subdomains). Covers repo views, file browser, issues, PRs, diffs, code search, settings.
- GitHub's site shell recolored to the ComfyDark surface palette.
- Diff row addition/deletion backgrounds retuned to sit on the ComfyDark base.
- GitHub syntax highlighting tokens (`--color-prettylights-syntax-*`) remapped to the VS Code ComfyDark syntax palette, so code on GitHub matches code in the editor.

Out of scope:

- `gist.github.com`, `raw.githubusercontent.com`, `docs.github.com`, `pages.github.com`, GitHub Marketplace.
- GitHub's light mode (extension is dark-only).
- AMO submission, Chrome Web Store packaging, or any signed distribution. Self-install as a temporary add-on only.
- Any JavaScript at runtime. CSS-only.

## Distribution

Sideloaded as a Firefox temporary add-on via `about:debugging#/runtime/this-firefox` → *Load Temporary Add-on* → pick `firefox/manifest.json`. Temporary add-ons are unloaded on Firefox restart; this is documented as a known tradeoff. Persistent unsigned installs require Firefox Developer Edition, Nightly, or the unbranded build.

No AMO submission, no signing, no auto-update channel.

## Folder layout

```
firefox/
  manifest.json
  comfydark.css
  icons/
    icon-48.png
    icon-96.png
```

`icon-48.png` and `icon-96.png` reuse or adapt the existing `vscode/images/icon.png`.

Root `README.md` gets a new `### Firefox` section under `## Install`, mirroring the style of the existing Zed/Obsidian/opencode entries.

## Manifest

Manifest V3, Firefox-targeted:

```json
{
  "manifest_version": 3,
  "name": "ComfyDark for GitHub",
  "version": "0.1.0",
  "description": "Applies the ComfyDark palette to github.com.",
  "icons": { "48": "icons/icon-48.png", "96": "icons/icon-96.png" },
  "content_scripts": [{
    "matches": ["*://github.com/*"],
    "css": ["comfydark.css"],
    "run_at": "document_start",
    "all_frames": true
  }],
  "browser_specific_settings": {
    "gecko": {
      "id": "comfydark@bechsor.no",
      "strict_min_version": "109.0"
    }
  }
}
```

Notes:

- `run_at: "document_start"` prevents a flash of GitHub's own colors before ours apply.
- No `permissions` declared. The content-script host match is the only capability the extension needs.
- `all_frames: true` so embedded frames (e.g. the reactions picker iframe) pick up the theme.

## CSS strategy

All work happens in `comfydark.css`. The file overrides CSS custom properties on `:root`; it does not target class names. GitHub's Primer design system ships these as public CSS variables, so the override surface is small, stable, and semantic.

Activation guard: the stylesheet only applies its overrides when GitHub is in its dark theme. GitHub sets `data-color-mode` and `data-dark-theme` on `<html>`, so the guard is written as:

```css
:root[data-color-mode="dark"][data-dark-theme*="dark"] { /* … */ }
```

`data-dark-theme*="dark"` matches `dark` and `dark_dimmed`. The implementation may narrow this if high-contrast or colorblind dark variants should be left alone. Light-mode users are unaffected. No attempt is made to force dark mode — if the user has picked light on GitHub, this extension does nothing.

Three override groups:

**1. Surface tokens.** Map GitHub's shell colors to the ComfyDark UI palette from `vscode/themes/comfydark.json`:

| Primer token | ComfyDark value |
| --- | --- |
| `--bgColor-default` | `#0d1117` |
| `--bgColor-muted`, `--bgColor-inset` | `#161b22` |
| `--borderColor-default`, `--borderColor-muted` | `#30363d` |
| `--fgColor-default` | `#c9d1d9` |
| `--fgColor-muted` | `#8b949e` |
| `--bgColor-accent-emphasis`, `--button-primary-bgColor-rest` | `#1f6feb` |
| `--fgColor-danger`, `--bgColor-danger-emphasis` | `#f85149` |
| `--fgColor-attention` | `#d29922` |

The full list in the implementation will include their nested variants (`-hover`, `-active`, `-selected`) where GitHub defines them.

**2. Diff row backgrounds.** Retune addition/deletion backgrounds so they sit on `#0d1117`:

- `--diffBlob-addition-bgColor-line`, `--diffBlob-addition-bgColor-word`
- `--diffBlob-deletion-bgColor-line`, `--diffBlob-deletion-bgColor-word`
- Matching number-column variants.

Values are low-saturation greens and reds tinted toward the ComfyDark base — dark enough not to glow, light enough to distinguish at a glance.

**3. Syntax tokens.** Remap PrettyLights to the VS Code ComfyDark palette. Pulled directly from `vscode/themes/comfydark.json`:

| PrettyLights token | ComfyDark value | Meaning |
| --- | --- | --- |
| `--color-prettylights-syntax-comment` | `#6A9955` | comments |
| `--color-prettylights-syntax-keyword` | `#569cd6` | keywords |
| `--color-prettylights-syntax-string` | `#ce9178` | strings |
| `--color-prettylights-syntax-string-regexp` | `#d16969` | regex |
| `--color-prettylights-syntax-constant` | `#b5cea8` | numeric constants |
| `--color-prettylights-syntax-variable` | `#9CDCFE` | variables |
| `--color-prettylights-syntax-entity` | `#DCDCAA` | function names |
| `--color-prettylights-syntax-entity-tag` | `#569cd6` | tag names |
| `--color-prettylights-syntax-storage-modifier-import` | `#d4d4d4` | imports |
| `--color-prettylights-syntax-markup-heading` | `#569cd6` | markdown headings |
| `--color-prettylights-syntax-markup-bold` | `#569cd6` | markdown bold |
| `--color-prettylights-syntax-markup-italic` | `#c9d1d9` | markdown italic |
| `--color-prettylights-syntax-markup-list` | `#6796e6` | markdown list markers |
| `--color-prettylights-syntax-markup-deleted-text` / `-bg` | `#ce9178` / tinted | markdown deletion |
| `--color-prettylights-syntax-markup-inserted-text` / `-bg` | `#b5cea8` / tinted | markdown insertion |
| `--color-prettylights-syntax-invalid-illegal-text` | `#f44747` | invalid tokens |
| `--color-prettylights-syntax-sublimelinter-gutter-mark` | `#8b949e` | gutter marks |

Any PrettyLights token not listed is left to fall back to the Primer default — better to leave GitHub's value than invent a mismatched one.

## Versioning

`firefox/manifest.json` uses its own `version` starting at `0.1.0`. It is not coupled to `vscode/package.json`. Releases are informal — a version bump is only meaningful for someone re-sideloading the add-on.

## README changes

Add a `### Firefox` section to root `README.md`, between the existing sections, following the "copy these files, then do this" ergonomics of the other ports:

```
### Firefox (GitHub only)

1. Open `about:debugging#/runtime/this-firefox` in Firefox.
2. Click *Load Temporary Add-on…* and select `firefox/manifest.json`.

Applies to `github.com` when GitHub is in dark mode. Unloads on browser restart — Developer Edition or Nightly will persist it across restarts.
```

## Success criteria

- Loading the temporary add-on on a fresh Firefox profile applies the palette to `github.com` without flicker and without any JS running.
- A diff view on GitHub uses ComfyDark surface colors, retuned diff row backgrounds, and VS Code syntax colors on added/removed lines.
- Switching GitHub to light mode removes all overrides (extension disables itself via the activation guard).
- Non-`github.com` tabs are untouched.
- The repo's other ports are unchanged.

## Non-goals

- Respecting user customisation (no options page, no popup, no toggles).
- Covering every GitHub subpage pixel-perfectly — we only override named tokens. If GitHub ships a surface that bypasses Primer tokens, it is expected to look off, and that is acceptable.
- Chasing GitHub UI changes. Maintenance is "update when tokens break", not "track every redesign".
