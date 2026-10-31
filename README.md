# Export Selected to DXF

An Autodesk Fusion add-in that exports whatever you have selected as **one DXF file per item**, from a dark dockable panel.

**[⬇ Download the latest version](https://github.com/swami-claude-skills/fusion-export-selected-to-dxf/releases/latest/download/ExportSelectedToDXF.zip)** · **[Dashboard](https://swami-claude-skills.github.io/fusion-export-selected-to-dxf/)** · **[All versions](https://github.com/swami-claude-skills/fusion-export-selected-to-dxf/releases)**

## What you can select

| You select | What gets exported |
|---|---|
| Every curve of a sketch, or a sketch in the browser | The whole sketch |
| Some curves of a sketch | Just those curves, at their original position |
| A planar face | The face outline |
| A solid body | Its largest flat face |
| A flat pattern, or a sheet-metal body or component | The flat pattern, with optional bend lines |

Units (design, mm, cm, m, in, ft), file naming, overwrite or auto-number, and whether to include construction geometry, sketch points and projected geometry are all set in the panel and remembered between sessions.

## Install

1. Download **ExportSelectedToDXF.zip** and unzip it.
2. Double-click **install-macos.command** (Mac; on first run you may need to right-click it and choose Open) or **install-windows.cmd** (Windows).
3. In Fusion press **Shift+S**, choose **ExportSelectedToDXF** under Add-Ins, and click **Run**. It runs automatically each time Fusion starts.

The button is in DESIGN under **SOLID ▸ CREATE** and **UTILITIES ▸ ADD-INS**. To give it a keyboard shortcut, right-click the button and choose **Change Keyboard Shortcut**.

## Updating

When the panel opens it checks [`version.json`](version.json) and shows a banner if a newer version exists. Download the zip, run its installer, then in Fusion press **Shift+S**, select ExportSelectedToDXF, click **Stop**, then **Run**. Your settings are kept.

## Repository layout

| Path | What it is |
|---|---|
| `ExportSelectedToDXF/` | The add-in itself (what the zip contains) |
| `version.json` | Latest version number, read by the add-in's update check |
| `docs/index.html` | The dashboard, served by GitHub Pages |
| `tools/build_release.py` | Builds `dist/ExportSelectedToDXF.zip` and refreshes `version.json` |
| `notes/vX.Y.Z.md` | Release notes for each version |
| `.github/workflows/release.yml` | When a new version reaches main, builds the zip and publishes the release |

Each release attaches the zip under the fixed name `ExportSelectedToDXF.zip`, so the download link above always gives the newest version.

---
Vibe Coding: Swami · AI: Claude
