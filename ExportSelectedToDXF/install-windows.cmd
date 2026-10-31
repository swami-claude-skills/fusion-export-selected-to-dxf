@echo off
REM Double-click installer (Windows). Set NAME to the add-in folder/.py/.manifest basename.
set "NAME=ExportSelectedToDXF"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-windows.ps1" -Name "%NAME%"
pause
