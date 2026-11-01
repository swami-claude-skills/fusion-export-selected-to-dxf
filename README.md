# Export Selected to DXF

An Autodesk Fusion add-in that exports whatever you have selected as **one DXF file per item**, from a dark dockable panel.

**[⬇ Download the latest version](https://github.com/swami-claude-skills/fusion-export-selected-to-dxf/releases/latest/download/ExportSelectedToDXF.zip)** · **[Documentation](https://swami-claude-skills.github.io/fusion-export-selected-to-dxf/)** · **[All versions](https://github.com/swami-claude-skills/fusion-export-selected-to-dxf/releases)**

## What you can select

| You select | What gets exported |
|---|---|
| Every curve of a sketch, or a sketch in the browser | The whole sketch |
| Some curves of a sketch | Just those curves, at their original position |
| A planar face | The face outline |
| A solid body | Its largest flat face |
| A flat pattern, or a sheet-metal body or component | The flat pattern, with optional bend lines (created first if the part doesn't have one yet) |

The panel's **Log** section records every export, skipped item, error and update, and saves it to `log.txt` in the add-in's settings folder; **copy** puts it on the clipboard to send when something goes wrong.

Units (design, mm, cm, m, in, ft), file naming, overwrite or auto-number, and whether to include construction geometry, sketch points and projected geometry are all set in the panel and remembered between sessions.

## Install

1. Download **ExportSelectedToDXF.zip** and unzip it. Put the **ExportSelectedToDXF** folder somewhere it can stay (for example a Fusion add-ins folder in Documents) — Fusion runs it from there.
2. In Fusion press **Shift+S** to open **Scripts and Add-Ins**, click the **+** next to **My Add-Ins**, and choose the **ExportSelectedToDXF** folder.
3. Turn on **Run on Startup** and **Run** for **ExportSelectedToDXF**.

This way nothing has to be approved in macOS Settings, because no installer script runs.

The button is in DESIGN under **SOLID ▸ CREATE** and **UTILITIES ▸ ADD-INS**. To give it a keyboard shortcut, right-click the button and choose **Change Keyboard Shortcut**.

**Alternative:** the zip also contains double-click installers (**install-macos.command**, **install-windows.cmd**) that copy the add-in into Fusion's own AddIns folder. On a Mac, macOS blocks the script the first time and it has to be allowed in **System Settings ▸ Privacy & Security**.

## Updating

When the panel opens it checks [`version.json`](version.json). If a newer version exists, a green banner offers **install update**: the add-in downloads the new version from this repository, backs up the current one, and replaces its own files. Then press **Shift+S** and turn ExportSelectedToDXF's **Run** switch off, then on (or restart Fusion). Your settings are kept. Versions before 1.3.0 don't have the button; update those by downloading the zip and replacing the folder.

## Repository layout

| Path | What it is |
|---|---|
| `ExportSelectedToDXF/` | The add-in itself (what the zip contains) |
| `version.json` | Latest version number, read by the add-in's update check |
| `docs/index.html` | The documentation, served by GitHub Pages |
| `tools/build_release.py` | Builds `dist/ExportSelectedToDXF.zip` and refreshes `version.json` |
| `notes/vX.Y.Z.md` | Release notes for each version (first line: `Released: <date>`) |
| `tools/build_docs.py` | Fills the documentation's version, date and What's New from the add-in and the notes |
| `.github/workflows/release.yml` | When a new version reaches main, checks the documentation is for that version, builds the zip and publishes the release |

## Releasing

1. Bump `VERSION` in the add-in and the manifest, and write `notes/vX.Y.Z.md`.
2. Update the documentation's content, then run `python3 tools/build_docs.py docs/index.html` to fill in the version, date and What's New.
3. Run `python3 tools/build_release.py` and push to `main`. The workflow refuses to publish if the documentation is for a different version.

Each release attaches the zip under the fixed name `ExportSelectedToDXF.zip`, so the download link above always gives the newest version.

---
Vibe Coding: Swami · AI: Claude
