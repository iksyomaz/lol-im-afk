$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

function Invoke-Native {
    & $args[0] @($args | Select-Object -Skip 1)
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $($args -join ' ')"
    }
}

$buildRoot = Join-Path $env:TEMP "lol-im-afk-pyinstaller-$PID"
if (Test-Path -LiteralPath $buildRoot) {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $buildRoot | Out-Null

Invoke-Native python -m pip install -e ".[build]"
Invoke-Native python -m unittest discover -s tests
Invoke-Native python -m compileall -q src tests
Invoke-Native python -m PyInstaller `
    --noconfirm `
    --clean `
    --noconsole `
    --onefile `
    --name lol-im-afk `
    --paths src `
    --hidden-import pystray._win32 `
    --collect-data sv_ttk `
    --distpath dist `
    --workpath (Join-Path $buildRoot "build") `
    --specpath $buildRoot `
    src\lol_im_afk\__main__.py

Write-Host "Built dist\lol-im-afk.exe"
