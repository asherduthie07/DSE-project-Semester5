"""Trusted local model registry with artifact checksum verification."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from ..cli import PROJECT_ROOT, sha256
from .tasks import MLError


def registry_path(root: Path = PROJECT_ROOT, *, quick: bool = False) -> Path:
    return root / "ml" / ("registry_quick.json" if quick else "registry.json")


def read_registry(root: Path = PROJECT_ROOT, *, quick: bool = False) -> dict[str, Any]:
    path = registry_path(root, quick=quick)
    if not path.is_file():
        raise MLError(f"Trained model registry missing: {path}; run mediscope ml train first")
    data = json.loads(path.read_text(encoding="utf-8"))
    if "tasks" not in data:
        raise MLError(f"Invalid model registry: {path}")
    return data


def load_model(task: str, algorithm: str | None = None, *, root: Path = PROJECT_ROOT, quick: bool = False) -> tuple[Any, dict[str, Any], str]:
    """Load only a registry-listed artifact under this project's model directory.

    joblib uses pickle and can execute code. Callers must trust the repository and
    locally generated artifacts. The hash guards accidental changes, not a hostile
    registry plus artifact pair.
    """
    registry = read_registry(root, quick=quick)
    if task not in registry["tasks"]:
        raise MLError(f"No trained model for {task}; run mediscope ml train --dataset {task}")
    entry = registry["tasks"][task]
    name = algorithm or entry["selected_model"]
    if name not in entry["trials"]:
        raise MLError(f"Algorithm {name!r} is absent from {task} registry")
    info = entry["trials"][name]["artifact"]
    expected_dir = (root / "ml" / "models" / ("quick" if quick else "full") / task).resolve()
    path = (root / info["path"]).resolve()
    if path.parent != expected_dir or path.suffix != ".joblib":
        raise MLError("Model artifact path escapes trusted project model directory")
    if not path.is_file() or sha256(path) != info["sha256"]:
        raise MLError(f"Model artifact missing or checksum mismatch: {path}")
    return joblib.load(path), entry, name
