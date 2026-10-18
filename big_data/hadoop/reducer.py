"""Hadoop Streaming reducer; Hadoop sorts keys before this stage."""
from __future__ import annotations

import sys


def reduce_lines(lines):
    current = None
    total = 0
    for line in lines:
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) != 2 or not parts[0] or parts[1] != "1":
            raise ValueError(f"Invalid mapper output: {line!r}")
        key = parts[0]
        if current is not None and key < current:
            raise ValueError("Mapper output is not sorted")
        if key != current:
            if current is not None:
                yield f"{current}\t{total}\n"
            current, total = key, 0
        total += 1
    if current is not None:
        yield f"{current}\t{total}\n"


if __name__ == "__main__":
    try:
        sys.stdout.writelines(reduce_lines(sys.stdin))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc
