# ComfyDark for Firefox

A static Firefox theme that applies the ComfyDark palette (GitHub Dark Default UI colors) to the browser chrome: tabs, toolbars, URL bar, menus, sidebar, and the new tab page.

This themes the browser UI itself. For GitHub syntax highlighting in page content, see [`../firefox-github`](../firefox-github).

## Color mapping

| Firefox element | Color | Source |
|---|---|---|
| Window frame / inactive tabs | `#0d1117` | `editor.background` |
| Toolbar / active tab | `#161b22` | `tab.activeBackground` |
| Text | `#c9d1d9` | `editor.foreground` |
| Inactive tab text | `#8b949e` | `tab.inactiveForeground` |
| Borders and separators | `#30363d` | `sideBar.border` |
| Active tab line, focus ring, highlights | `#1f6feb` | `button.background` / `focusBorder` |
| URL bar selection | `#264f78` | `editor.selectionBackground` |

The URL bar uses `#0d1117` (one step darker than the toolbar) so it stands out against the `#161b22` toolbar, mirroring how inputs sit against panels in the editor themes.

## Install (Firefox Developer Edition)

Developer Edition allows permanently installing unsigned add-ons:

1. Open `about:config` and set `xpinstall.signatures.required` to `false`.
2. Open `about:addons`, click the gear icon → **Install Add-on From File…**
3. Select `comfydark.xpi`.

To rebuild the `.xpi` after changing colors:

```sh
cd firefox-theme && zip -j comfydark.xpi manifest.json
```

### Temporary install (any Firefox)

Open `about:debugging#/runtime/this-firefox` → **Load Temporary Add-on…** → select `manifest.json`. Lasts until the browser restarts.
