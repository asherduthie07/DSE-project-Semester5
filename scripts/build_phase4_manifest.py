"""Build or verify SHA-256 manifest for the generated full Phase IV artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports" / "ml" / "artifact_manifest.json"
SOURCES = (ROOT / "ml" / "models" / "full", ROOT / "reports" / "ml" / "full",
           ROOT / "reports" / "tables" / "ml", ROOT / "reports" / "figures" / "ml" / "full")


def inventory() -> dict[str, object]:
    files = sorted(path for directory in SOURCES for path in directory.rglob("*") if path.is_file())
    return {"format": "mediscope-phase4-artifacts-v1", "artifact_count": len(files),
            "files": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare current full artifacts with the saved manifest")
    args = parser.parse_args()
    current = inventory()
    if args.check:
        if not MANIFEST.is_file() or json.loads(MANIFEST.read_text()) != current:
            parser.exit(1, "Phase IV artifact manifest mismatch or missing file\n")
        print(f"PASS: {current['artifact_count']} Phase IV artifacts match SHA-256 manifest")
    else:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(f"Wrote {MANIFEST}: {current['artifact_count']} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
