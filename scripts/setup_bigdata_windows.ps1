$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'BLOCKED: Docker CLI is unavailable' }
docker compose version
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED: Docker Compose is unavailable' }
docker info | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED: Docker daemon is unavailable' }
docker compose -f docker/compose.bigdata.yml up -d --build --wait --wait-timeout 180
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose startup failed' }
python -m scripts.verify_bigdata
