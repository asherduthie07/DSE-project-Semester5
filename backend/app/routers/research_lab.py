"""Checksum-verified, static Phase VII research outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from backend.app.core.errors import APIError
from backend.app.core.config import Settings

router = APIRouter(prefix="/research-lab", tags=["research-lab"])
TASKS = ("heart", "diabetes", "stroke")
EXPORTS = ("comparisons.csv", "subgroups.csv", "importance.csv", "importance_stability.csv", "thresholds.csv",
           "heart_comparison.png", "diabetes_comparison.png", "stroke_comparison.png",
           "heart_calibration.png", "diabetes_calibration.png", "stroke_calibration.png")


def _verified(task: str | None = None) -> tuple[Path, dict]:
    folder = Settings.from_env().project_root / "reports/phase7"
    path = folder / "manifest.json"
    if not path.is_file():
        raise APIError(503, "RESEARCH_UNAVAILABLE", "Verified Phase VII outputs are unavailable.")
    manifest = json.loads(path.read_text())
    required = [f"reports/phase7/{task}.json"] if task else [f"reports/phase7/{t}.json" for t in TASKS]
    for relative in required:
        artifact = Settings.from_env().project_root / relative
        if not artifact.is_file() or manifest.get("artifacts", {}).get(relative) != hashlib.sha256(artifact.read_bytes()).hexdigest():
            raise APIError(503, "RESEARCH_UNAVAILABLE", "Phase VII artifact checksum verification failed.")
    return folder, manifest


@router.get("")
def overview() -> dict:
    folder, manifest = _verified()
    return {"version": manifest["version"], "seed": manifest["seed"],
            "tasks": [{"task": task, "dataset_id": data["dataset_id"], "development_n": data["development_n"],
                       "development_positive_n": data["development_positive_n"], "split_sha256": data["split_sha256"]}
                      for task in TASKS for data in [json.loads((folder/f"{task}.json").read_text())]],
            "exports": list(EXPORTS), "warning": "Research and education only; no clinical validation."}


@router.get("/exports/{filename}")
def export_file(filename: str):
    if filename not in EXPORTS:
        raise APIError(404, "NOT_FOUND", "Unknown research export.")
    folder, manifest = _verified()
    path = folder / filename
    relative = f"reports/phase7/{filename}"
    if not path.is_file() or manifest.get("artifacts", {}).get(relative) != hashlib.sha256(path.read_bytes()).hexdigest():
        raise APIError(503, "RESEARCH_UNAVAILABLE", "Research export verification failed.")
    return FileResponse(path, filename=filename)


@router.get("/{task}")
def detail(task: str) -> dict:
    if task not in TASKS:
        raise APIError(404, "NOT_FOUND", "Unknown research task.")
    folder, _ = _verified(task)
    return json.loads((folder/f"{task}.json").read_text())
