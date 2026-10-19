"""Curated research artifacts; callers cannot choose a filesystem path."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.core.errors import missing, unavailable


REPORTS = {
    "phase1-methodology": ("Phase I data preparation", "docs/PHASE1_DATA_PREPARATION.md"),
    "phase2-findings": ("Phase II statistical findings", "docs/PHASE2_FINDINGS.md"),
    "phase3-verification": ("Phase III visualization and Power BI status", "docs/PHASE3_VERIFICATION.md"),
    "phase4-findings": ("Phase IV model findings", "docs/PHASE4_FINDINGS.md"),
    "model-limitations": ("Research model limitations", "docs/MODEL_LIMITATIONS.md"),
    "phase5-verification": ("Phase V live MongoDB and Hadoop evidence", "docs/PHASE5_VERIFICATION.md"),
    "powerbi-windows": ("Power BI Windows build instructions", "docs/POWERBI_WINDOWS_SETUP.md"),
    "powerbi-macos": ("Power BI macOS Service instructions", "docs/POWERBI_MACOS_SETUP.md"),
}
CHARTS = {
    "heart-outcome": "reports/figures/phase3/heart_outcome_pie.png",
    "diabetes-symptoms": "reports/figures/phase3/diabetes_positive_symptom_frequencies.png",
    "stroke-age": "reports/figures/phase3/stroke_age_group_share_histogram.png",
    "synthea-encounters": "reports/figures/eda/synthea_csv_encounter_class_frequency.png",
}


class ArtifactService:
    def __init__(self, root: Path) -> None:
        self.root = root

    def listing(self) -> dict[str, Any]:
        reports = [{"key": key, "title": title, "available": (self.root / path).is_file()} for key, (title, path) in REPORTS.items()]
        charts = [{"key": key, "path": path, "available": (self.root / path).is_file()} for key, path in CHARTS.items()]
        return {"reports": reports, "charts": charts,
                "powerbi": {"static_artifacts": (self.root / "powerbi/exports/v1/manifest.json").is_file(),
                            "desktop_runtime": "NOT_VERIFIED", "service_publishing": "NOT_VERIFIED",
                            "instructions": ["powerbi-windows", "powerbi-macos"]}}

    def get(self, key: str) -> dict[str, Any]:
        if key not in REPORTS:
            raise missing("report")
        title, relative = REPORTS[key]
        try:
            content = (self.root / relative).read_text(encoding="utf-8")
        except OSError as exc:
            raise unavailable("Approved report") from exc
        return {"key": key, "title": title, "format": "markdown", "content": content}
