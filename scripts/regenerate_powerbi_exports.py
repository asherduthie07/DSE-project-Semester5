"""Regenerate portable aggregates from verified Phase I and II local outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mediscope.visualization.exports import build_exports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notes-dir", type=Path, help="Official Synthea note files from an independent run")
    args = parser.parse_args()
    print(json.dumps(build_exports(notes_dir=args.notes_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
