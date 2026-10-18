"""Generate source-only Phase V reference tables and chart; no service claim."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from big_data.mongodb.import_data import ROOT, read_source


def main() -> None:
    table_dir = ROOT / "reports/tables/bigdata"
    figure_dir = ROOT / "reports/figures/bigdata"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, field in (("heart", "heart_disease_binary"), ("diabetes", "class"), ("stroke", "stroke"),
                        ("patients", "GENDER"), ("encounters", "ENCOUNTERCLASS")):
        frame, digest = read_source(name)
        counts = frame[field].value_counts(dropna=False).sort_index()
        path = table_dir / f"source_{name}_counts.csv"
        counts.rename_axis(field).reset_index(name="count").to_csv(path, index=False)
        result[name] = {"source_sha256": digest, "rows": len(frame), "counts": {str(k): int(v) for k, v in counts.items()}}
    frame, _ = read_source("stroke")
    frame.groupby("stroke", dropna=False)["avg_glucose_level"].agg(["count", "mean"]).to_csv(table_dir / "source_glucose_by_stroke.csv")
    encounters, _ = read_source("encounters")
    visits = encounters.groupby("PATIENT").size()
    visits.value_counts().sort_index().rename_axis("encounters_per_patient").reset_index(name="patients").to_csv(table_dir / "source_patient_visit_distribution.csv", index=False)
    encounters.assign(month=encounters["START"].str.slice(0, 7)).groupby("month").size().rename("encounters").to_csv(table_dir / "source_monthly_encounters.csv")
    counts = encounters["ENCOUNTERCLASS"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(9, 5))
    counts.plot.barh(ax=ax, color="#277da1")
    ax.set(xlabel="Synthetic encounters", ylabel="Encounter class", title="Synthea encounter counts from prepared CSV")
    fig.tight_layout()
    fig.savefig(figure_dir / "source_encounters_by_class.png", dpi=180)
    plt.close(fig)
    (ROOT / "reports/bigdata").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports/bigdata/source_reference.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
