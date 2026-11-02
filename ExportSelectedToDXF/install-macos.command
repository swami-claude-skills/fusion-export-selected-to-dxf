#!/bin/bash
# Double-click installer (macOS). Set NAME to the add-in folder/.py/.manifest basename.
NAME="ExportSelectedToDXF"

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/$NAME"

echo "Installing $NAME -> $DEST"
mkdir -p "$DEST"
# copy everything except the installers themselves
rsync -a --delete \
  --exclude 'install-macos.command' \
  --exclude 'install-windows.cmd' \
  --exclude 'install-windows.ps1' \
  --exclude 'READ ME FIRST.txt' \
  "$SRC"/ "$DEST"/

# The add-in was called ExportSelectedDXF before v1.2.0. Move that old copy to the Trash
# so Fusion doesn't load two of them (its settings are carried over automatically).
OLD="$HOME/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/ExportSelectedDXF"
if [ -d "$OLD" ]; then
  mv "$OLD" "$HOME/.Trash/ExportSelectedDXF-$(date +%Y%m%d-%H%M%S)" && \
    echo "Moved the old ExportSelectedDXF add-in to the Trash (restart Fusion to unload it)."
fi

echo ""
echo "Done. In Fusion: Utilities > Add-Ins > Scripts and Add-Ins (Shift+S),"
echo "select \"$NAME\" under Add-Ins, and click Run."
echo ""
read -n 1 -s -r -p "Press any key to close."
