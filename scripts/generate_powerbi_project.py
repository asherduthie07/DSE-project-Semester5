"""Generate reviewable PBIP/PBIR/TMDL source from the versioned aggregate contract.

Power BI Desktop runtime validation is a separate acceptance gate. This script does
not produce a PBIX or assert that Desktop can render the project.
"""
from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path

from mediscope.cli import PROJECT_ROOT
from mediscope.visualization.exports import EXPORT_NAMES, verify_exports

ROOT = PROJECT_ROOT
BASE = ROOT / "powerbi"
MODEL = BASE / "MediScopeAI.SemanticModel"
REPORT = BASE / "MediScopeAI.Report"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric"
DATA_ROOT_TOKEN = "__MEDISCOPE_DATA_ROOT__"

# Numeric types are declared only for fields that contain numeric quantities.
INTEGER = {"rows", "columns", "count", "n", "nonmissing_n", "all_n", "group_n", "yes_n", "class_n", "missing_n", "missing_cells", "exact_duplicates", "exact_duplicates_retained", "records", "stroke_positive", "positive_n", "negative_n", "encounters", "patients", "synthetic", "value", "dof", "levels", "target_levels", "expected_below_5", "stroke_positive_n", "stroke_negative_n"}
DECIMAL = {"pct_all", "pct_nonmissing", "pct_within_age_group", "yes_pct", "stroke_pct", "missing_pct", "iqr_outliers_n", "bin_start", "bin_end", "min", "q1", "median", "q3", "max", "iqr", "mean", "mode", "range", "variance", "std", "skewness", "coefficient", "p_value", "bh_q_value", "chi2", "cramers_v", "minimum_expected", "statistic", "df", "effect_size", "ci_low", "ci_high", "alpha", "sensitivity_p_value", "positive_mean", "negative_mean", "positive_sd", "negative_sd", "positive_median", "negative_median", "positive_skew", "negative_skew", "mean_difference", "risk_difference", "phi", "stroke_risk_hypertension", "stroke_risk_no_hypertension"}
# Numeric-looking category labels remain text.
TEXT_OVERRIDE = {"outcome", "category", "group", "dataset_id", "age_group", "class", "bin_label", "month", "id", "feature", "target", "method", "positive_label", "negative_label", "source_id"}

VIEWS = {
    "heart_outcomes": ("outcomes", "uci_cleveland_heart"),
    "heart_age_groups": ("age_groups", "uci_cleveland_heart"),
    "heart_histogram": ("histogram_bins", "uci_cleveland_heart"),
    "heart_correlations": ("correlations", "uci_cleveland_heart"),
    "heart_hypothesis": ("hypotheses", "uci_cleveland_heart"),
    "diabetes_outcomes": ("outcomes", "uci_early_diabetes"),
    "diabetes_age_groups": ("age_groups", "uci_early_diabetes"),
    "diabetes_symptom_view": ("diabetes_symptoms", "uci_early_diabetes"),
    "stroke_outcomes": ("outcomes", "kaggle_stroke"),
    "stroke_age_groups": ("age_groups", "kaggle_stroke"),
    "stroke_risk_view": ("stroke_risk_factors", "kaggle_stroke"),
    "stroke_histogram": ("histogram_bins", "kaggle_stroke"),
    "stroke_hypotheses": ("hypotheses", "kaggle_stroke"),
}


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def columns_for(name: str) -> list[str]:
    with (BASE / "exports" / "v1" / f"{name}.csv").open(encoding="utf-8", newline="") as stream:
        return next(csv.reader(stream))


def dtype(column: str) -> tuple[str, str]:
    if column in TEXT_OVERRIDE:
        return "string", "type text"
    if column in INTEGER:
        return "int64", "Int64.Type"
    if column in DECIMAL:
        return "double", "type number"
    return "string", "type text"


def write_table(name: str, source_name: str, *, dataset_id: str | None = None) -> None:
    cols = columns_for(source_name)
    if dataset_id and "dataset_id" not in cols:
        raise ValueError(f"Cannot filter {source_name} by dataset_id")
    lines = [f"table {name}"]
    for column in cols:
        kind, _ = dtype(column)
        lines.extend([f"\tcolumn {column}", f"\t\tdataType: {kind}", f"\t\tsourceColumn: {column}", "\t\tsummarizeBy: none", ""])
    for column in cols:
        if column in {"count", "rows", "missing_n", "encounters", "patients", "yes_pct", "stroke_pct"}:
            aggregate = "AVERAGE" if column.endswith("_pct") else "SUM"
            lines.extend([f"\tmeasure 'Total {column}' = {aggregate}({name}[{column}])", "\t\tformatString: #,##0.00" if aggregate == "AVERAGE" else "\t\tformatString: #,##0", ""])
    lines.extend([f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =", "\t\t\tlet",
                  f'\t\t\t\tSource = Csv.Document(File.Contents(DataRoot & "\\{source_name}.csv"), [Delimiter=",", Columns={len(cols)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
                  '\t\t\t\tHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
                  '\t\t\t\tNulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),',
                  "\t\t\t\tTyped = Table.TransformColumnTypes(Nulls, {" + ", ".join('{"' + col + '", ' + dtype(col)[1] + '}' for col in cols) + '}, "en-US")' + ("," if dataset_id else "")])
    if dataset_id:
        lines.append(f'\t\t\t\tFiltered = Table.SelectRows(Typed, each [dataset_id] = "{dataset_id}")')
    lines.append("\t\t\tin " + ("Filtered" if dataset_id else "Typed"))
    (MODEL / "definition" / "tables" / f"{name}.tmdl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def field(table: str, column: str, measure: bool = False) -> dict:
    kind = "Measure" if measure else "Column"
    return {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}


def projection(table: str, column: str, measure: bool = False) -> dict:
    return {"field": field(table, column, measure), "queryRef": f"{table}.{column}", "nativeQueryRef": column}


def visual(page: Path, name: str, visual_type: str, roles: dict[str, list[tuple[str, str, bool]]], pos: tuple[int, int, int, int], order: int) -> None:
    x, y, width, height = pos
    query_state = {role: {"projections": [projection(*item) for item in items]} for role, items in roles.items()}
    spec = {"$schema": f"{SCHEMA}/item/report/definition/visualContainer/2.0.0/schema.json", "name": name,
            "position": {"x": x, "y": y, "z": order, "width": width, "height": height, "tabOrder": order},
            "visual": {"visualType": visual_type, "query": {"queryState": query_state}}}
    dump(page / "visuals" / name / "visual.json", spec)


def plot(page: Path, name: str, table: str, xcol: str, ycol: str, pos: tuple[int, int, int, int], *, series: str | None = None, chart: str = "clusteredColumnChart") -> None:
    roles: dict[str, list[tuple[str, str, bool]]] = {"Category": [(table, xcol, False)], "Y": [(table, f"Total {ycol}", True)]}
    if series:
        roles["Series"] = [(table, series, False)]
    visual(page, name, chart, roles, pos, len(list(page.glob("visuals/*"))) + 1)


def table_visual(page: Path, name: str, table: str, cols: list[str], pos: tuple[int, int, int, int]) -> None:
    visual(page, name, "tableEx", {"Values": [(table, col, False) for col in cols]}, pos, len(list(page.glob("visuals/*"))) + 1)


def slicer(page: Path, name: str, table: str, column: str, pos: tuple[int, int, int, int]) -> None:
    visual(page, name, "slicer", {"Values": [(table, column, False)]}, pos, len(list(page.glob("visuals/*"))) + 1)


def main() -> int:
    verify_exports()
    BASE.mkdir(exist_ok=True)
    MODEL.joinpath("definition", "tables").mkdir(parents=True, exist_ok=True)
    REPORT.joinpath("definition", "pages").mkdir(parents=True, exist_ok=True)
    dump(BASE / "MediScopeAI.pbip", {"$schema": f"{SCHEMA}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0", "artifacts": [{"report": {"path": "MediScopeAI.Report"}}]})
    dump(MODEL / "definition.pbism", {"$schema": f"{SCHEMA}/item/semanticModel/definitionProperties/1.0.0/schema.json", "version": "4.2", "settings": {"qnaEnabled": False}})
    (MODEL / "definition" / "model.tmdl").write_text("model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n\tsourceQueryCulture: en-US\n", encoding="utf-8")
    (MODEL / "definition" / "expressions.tmdl").write_text(f'''expression DataRoot = "{DATA_ROOT_TOKEN}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n''', encoding="utf-8")
    for name in EXPORT_NAMES:
        write_table(name, name)
    for name, (source, dataset) in VIEWS.items():
        write_table(name, source, dataset_id=dataset)
    relationships = []
    for name in EXPORT_NAMES:
        if name not in ("dataset_dimension", "note_terms") and "dataset_id" in columns_for(name):
            rid = uuid.uuid5(uuid.NAMESPACE_URL, f"mediscope:{name}:dataset_id")
            relationships.append(f"relationship {rid}\n\tfromColumn: {name}.dataset_id\n\ttoColumn: dataset_dimension.dataset_id\n")
    (MODEL / "definition" / "relationships.tmdl").write_text("\n".join(relationships), encoding="utf-8")
    (MODEL / "definition" / "tables" / "dataset_dimension.tmdl").write_text((MODEL / "definition" / "tables" / "dataset_dimension.tmdl").read_text(encoding="utf-8") + '''\n\tmeasure 'Distinct registered datasets' = DISTINCTCOUNT(dataset_dimension[dataset_id])\n\t\tformatString: #,##0\n''', encoding="utf-8")
    dump(REPORT / "definition.pbir", {"$schema": f"{SCHEMA}/item/report/definitionProperties/2.0.0/schema.json", "version": "4.0", "datasetReference": {"byPath": {"path": "../MediScopeAI.SemanticModel"}}})
    definition = REPORT / "definition"
    dump(definition / "version.json", {"$schema": f"{SCHEMA}/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    dump(definition / "report.json", {"$schema": f"{SCHEMA}/item/report/definition/report/3.1.0/schema.json", "themeCollection": {}})
    pages = [
        ("overview", "Executive overview"), ("heart", "Heart disease"), ("diabetes", "Diabetes"),
        ("stroke", "Stroke"), ("hospital", "Synthetic hospital"), ("quality", "Data quality and research")]
    dump(definition / "pages" / "pages.json", {"$schema": f"{SCHEMA}/item/report/definition/pagesMetadata/1.0.0/schema.json", "pageOrder": [p for p, _ in pages], "activePageName": "overview"})
    for name, title in pages:
        page = definition / "pages" / name
        dump(page / "page.json", {"$schema": f"{SCHEMA}/item/report/definition/page/2.0.0/schema.json", "name": name, "displayName": title, "displayOption": "FitToPage", "height": 720, "width": 1280})
    pg = definition / "pages"
    overview = pg / "overview"
    slicer(overview, "dataset_selector", "dataset_dimension", "display_name", (20, 20, 260, 100))
    table_visual(overview, "dataset_overview_table", "dataset_overview", ["display_name", "analysis_unit", "rows", "missing_cells", "exact_duplicates"], (300, 20, 950, 220))
    plot(overview, "outcome_distribution", "outcomes", "category", "count", (20, 270, 610, 400), series="dataset_id")
    table_visual(overview, "source_details", "dataset_dimension", ["display_name", "provenance", "source_url"], (650, 270, 600, 400))
    heart = pg / "heart"
    slicer(heart, "heart_outcome_slicer", "heart_outcomes", "category", (20, 20, 250, 90))
    plot(heart, "heart_outcome_chart", "heart_outcomes", "category", "count", (290, 20, 450, 280))
    plot(heart, "heart_age_chart", "heart_age_groups", "age_group", "count", (760, 20, 490, 280), series="outcome")
    plot(heart, "heart_age_hist", "heart_histogram", "bin_label", "count", (20, 330, 610, 350), series="outcome")
    table_visual(heart, "heart_research", "heart_hypothesis", ["id", "positive_n", "negative_n", "mean_difference", "p_value", "effect_size", "ci_low", "ci_high"], (650, 330, 600, 160))
    table_visual(heart, "heart_correlation", "heart_correlations", ["method", "left", "right", "coefficient", "n"], (650, 510, 600, 170))
    diabetes = pg / "diabetes"
    slicer(diabetes, "diabetes_outcome_slicer", "diabetes_outcomes", "category", (20, 20, 250, 90))
    plot(diabetes, "diabetes_outcomes_chart", "diabetes_outcomes", "category", "count", (290, 20, 450, 280))
    plot(diabetes, "diabetes_age_chart", "diabetes_age_groups", "age_group", "count", (760, 20, 490, 280), series="outcome")
    plot(diabetes, "symptom_chart", "diabetes_symptom_view", "symptom", "yes_pct", (20, 330, 760, 350), series="class", chart="clusteredBarChart")
    table_visual(diabetes, "diabetes_quality", "dataset_overview", ["display_name", "rows", "exact_duplicates"], (800, 330, 450, 350))
    stroke = pg / "stroke"
    slicer(stroke, "stroke_outcome_slicer", "stroke_outcomes", "category", (20, 20, 250, 90))
    plot(stroke, "stroke_outcome_chart", "stroke_outcomes", "category", "count", (290, 20, 450, 280))
    plot(stroke, "stroke_age_chart", "stroke_age_groups", "age_group", "count", (760, 20, 490, 280), series="outcome")
    plot(stroke, "stroke_risk_chart", "stroke_risk_view", "factor", "stroke_pct", (20, 330, 610, 350), series="value")
    table_visual(stroke, "stroke_research", "stroke_hypotheses", ["id", "method", "p_value", "effect_size", "ci_low", "ci_high"], (650, 330, 600, 350))
    hospital = pg / "hospital"
    slicer(hospital, "hospital_category_slicer", "synthea_encounter_classes", "category", (20, 20, 250, 110))
    plot(hospital, "encounter_categories", "synthea_encounter_classes", "category", "count", (290, 20, 460, 300))
    plot(hospital, "encounter_trend", "synthea_monthly_encounters", "month", "encounters", (770, 20, 480, 300), chart="lineChart")
    plot(hospital, "encounters_per_patient", "synthea_encounters_per_patient", "encounters", "patients", (20, 340, 610, 340))
    plot(hospital, "ages_at_encounter", "synthea_age_at_encounter", "age_group", "encounters", (650, 340, 600, 340))
    quality = pg / "quality"
    slicer(quality, "quality_dataset_slicer", "dataset_dimension", "display_name", (20, 20, 260, 110))
    plot(quality, "missing_values", "quality_metrics", "feature", "missing_n", (300, 20, 950, 260))
    table_visual(quality, "quality_table", "quality_metrics", ["table_name", "feature", "rows", "missing_n", "iqr_outliers_n", "exact_duplicates_retained"], (20, 310, 610, 370))
    table_visual(quality, "hypothesis_table", "hypotheses", ["id", "method", "positive_n", "negative_n", "p_value", "effect_size", "ci_low", "ci_high"], (650, 310, 600, 370))
    print(json.dumps({"pbip": str(BASE / "MediScopeAI.pbip"), "pages": len(pages), "tables": len(EXPORT_NAMES) + len(VIEWS), "desktop_runtime": "NOT TESTED"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
