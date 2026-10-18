param([switch]$ValidateOnly, [int]$Port = 8765)
$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $ProjectRoot
try {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python launcher py.exe is required. Install Python 3.11 or newer.' }
    & py -3 -m dashboard.app --check
    if ($LASTEXITCODE -ne 0) { throw 'Bundled dashboard validation failed.' }
    if ($ValidateOnly) { exit 0 }
    Write-Host "Open http://127.0.0.1:$Port/ in your browser. Press Ctrl+C to stop."
    & py -3 -m dashboard.app --host 127.0.0.1 --port $Port
    exit $LASTEXITCODE
} finally { Pop-Location }
