$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

python -m pip install -e ".[build]"
python -m unittest discover -s tests
python -m compileall -q src tests
python -m PyInstaller `
    --noconfirm `
    --clean `
    --noconsole `
    --onefile `
    --name lol-im-afk `
    --paths src `
    --hidden-import pystray._win32 `
    --collect-data sv_ttk `
    src\lol_im_afk\__main__.py

Write-Host "Built dist\lol-im-afk.exe"
