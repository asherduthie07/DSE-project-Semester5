#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo 'BLOCKED: Docker CLI is unavailable' >&2; exit 2; }
docker compose version >/dev/null || { echo 'BLOCKED: Docker Compose is unavailable' >&2; exit 2; }
docker info >/dev/null || { echo 'BLOCKED: Docker daemon is unavailable' >&2; exit 2; }
docker compose -f docker/compose.bigdata.yml up -d --build --wait --wait-timeout 180
.venv/bin/python -m scripts.verify_bigdata
