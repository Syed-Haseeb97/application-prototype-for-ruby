# Build dist\Ruby\Ruby.exe (run from the repo root on Windows, venv active).
$ErrorActionPreference = "Stop"
python -m pip install -r requirements-build.txt
python packaging\make_icon.py
pyinstaller --noconfirm ruby.spec
if (-not (Test-Path "dist\Ruby\Ruby.exe")) { throw "Build failed: dist\Ruby\Ruby.exe not found" }
Write-Host "Built dist\Ruby\Ruby.exe. Next: scripts\create_shortcuts.ps1 (or build installer\ruby.iss with Inno Setup)."
