#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.11 or newer is required. Install Python, then rerun this script." >&2
  exit 2
fi
python3 -m dashboard.app --check
if [[ "${1:-}" == "--check" ]]; then
  exit 0
fi
echo "Open http://127.0.0.1:8765/ in your browser. Press Ctrl+C to stop."
exec python3 -m dashboard.app --host 127.0.0.1 --port 8765
