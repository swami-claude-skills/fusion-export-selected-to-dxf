param([string]$Name = "ExportSelectedToDXF")

$src  = Split-Path -Parent $MyInvocation.MyCommand.Path
$dest = Join-Path $env:APPDATA "Autodesk\Autodesk Fusion 360\API\AddIns\$Name"

Write-Host "Installing $Name -> $dest"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$exclude = @('install-macos.command','install-windows.cmd','install-windows.ps1','READ ME FIRST.txt')
Get-ChildItem -Path $src -Recurse | Where-Object {
    $exclude -notcontains $_.Name
} | ForEach-Object {
    $rel = $_.FullName.Substring($src.Length).TrimStart('\')
    $target = Join-Path $dest $rel
    if ($_.PSIsContainer) {
        New-Item -ItemType Directory -Force -Path $target | Out-Null
    } else {
        New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
        Copy-Item $_.FullName -Destination $target -Force
    }
}

# The add-in was called ExportSelectedDXF before v1.2.0. Remove that old copy so Fusion
# doesn't load two of them (its settings are carried over automatically).
$old = Join-Path $env:APPDATA "Autodesk\Autodesk Fusion 360\API\AddIns\ExportSelectedDXF"
if (Test-Path $old) {
    Remove-Item -Recurse -Force $old -ErrorAction SilentlyContinue
    Write-Host "Removed the old ExportSelectedDXF add-in (restart Fusion to unload it)."
}

Write-Host ""
Write-Host "Done. In Fusion: Utilities > Add-Ins > Scripts and Add-Ins (Shift+S),"
Write-Host "select `"$Name`" under Add-Ins, and click Run."
