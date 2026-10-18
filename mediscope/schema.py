"""Dataset-specific Phase I domain rules and model feature roles.

Bounds are deliberately broad impossibility checks, not clinical reference ranges.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TableSchema:
    """Machine-checkable source value rules for one registered table."""

    numeric: dict[str, tuple[float | None, float | None]] = field(default_factory=dict)
    integer: tuple[str, ...] = ()
    categories: dict[str, tuple[str, ...]] = field(default_factory=dict)
    dates: tuple[str, ...] = ()
    required_text: tuple[str, ...] = ()
    unique_key: tuple[str, ...] = ()
    record_key: tuple[str, ...] = ()
    continuous: tuple[str, ...] = ()
    binary: dict[str, tuple[str, str]] = field(default_factory=dict)
    nominal: tuple[str, ...] = ()
    ordinal: dict[str, tuple[str, ...]] = field(default_factory=dict)
    excluded_from_model: tuple[str, ...] = ()


YES_NO = ("No", "Yes")
HEART = TableSchema(
    numeric={"age": (0, 120), "trestbps": (0, 400), "chol": (0, 1000), "thalach": (0, 300), "oldpeak": (0, 20), "num": (0, 4)},
    integer=("age", "trestbps", "chol", "thalach", "num"),
    categories={"sex": ("0", "1"), "cp": ("1", "2", "3", "4"), "fbs": ("0", "1"), "restecg": ("0", "1", "2"), "exang": ("0", "1"), "slope": ("1", "2", "3"), "ca": ("0", "1", "2", "3"), "thal": ("3", "6", "7")},
    continuous=("age", "trestbps", "chol", "thalach", "oldpeak"),
    binary={"sex": ("0", "1"), "fbs": ("0", "1"), "exang": ("0", "1")},
    nominal=("cp", "restecg", "slope", "ca", "thal"),
    excluded_from_model=("num", "heart_disease_binary"),
)
DIABETES_SYMPTOMS = ("Polyuria", "Polydipsia", "sudden weight loss", "weakness", "Polyphagia", "Genital thrush", "visual blurring", "Itching", "Irritability", "delayed healing", "partial paresis", "muscle stiffness", "Alopecia", "Obesity")
DIABETES = TableSchema(
    numeric={"Age": (0, 120)}, integer=("Age",),
    categories={"Gender": ("Female", "Male"), **{name: YES_NO for name in DIABETES_SYMPTOMS}, "class": ("Negative", "Positive")},
    continuous=("Age",), binary={name: YES_NO for name in DIABETES_SYMPTOMS},
    nominal=("Gender",), excluded_from_model=("class",),
)
STROKE = TableSchema(
    numeric={"id": (0, None), "age": (0, 120), "avg_glucose_level": (0, 1000), "bmi": (0, 150), "stroke": (0, 1)},
    integer=("id", "stroke"),
    categories={"gender": ("Female", "Male", "Other"), "hypertension": ("0", "1"), "heart_disease": ("0", "1"), "ever_married": YES_NO, "work_type": ("Govt_job", "Never_worked", "Private", "Self-employed", "children"), "Residence_type": ("Rural", "Urban"), "smoking_status": ("formerly smoked", "never smoked", "smokes")},
    required_text=("id",), unique_key=("id",), record_key=("id",),
    continuous=("age", "avg_glucose_level", "bmi"),
    binary={"hypertension": ("0", "1"), "heart_disease": ("0", "1"), "ever_married": YES_NO},
    nominal=("gender", "work_type", "Residence_type", "smoking_status"),
    excluded_from_model=("id", "stroke"),
)
PATIENTS = TableSchema(
    numeric={"LAT": (-90, 90), "LON": (-180, 180), "HEALTHCARE_EXPENSES": (0, None), "HEALTHCARE_COVERAGE": (0, None)},
    dates=("BIRTHDATE", "DEATHDATE"), required_text=("Id", "BIRTHDATE"),
    unique_key=("Id",), record_key=("Id",),
    continuous=("LAT", "LON", "HEALTHCARE_EXPENSES", "HEALTHCARE_COVERAGE"),
)
ENCOUNTERS = TableSchema(
    numeric={"BASE_ENCOUNTER_COST": (0, None), "TOTAL_CLAIM_COST": (0, None), "PAYER_COVERAGE": (0, None)},
    dates=("START", "STOP"), required_text=("Id", "PATIENT", "START"),
    unique_key=("Id",), record_key=("PATIENT", "START", "CODE"),
    continuous=("BASE_ENCOUNTER_COST", "TOTAL_CLAIM_COST", "PAYER_COVERAGE"),
)

SCHEMAS: dict[str, dict[str, TableSchema]] = {
    "uci_cleveland_heart": {"processed.cleveland.data": HEART},
    "uci_early_diabetes": {"diabetes_data_upload.csv": DIABETES},
    "kaggle_stroke": {"healthcare-dataset-stroke-data.csv": STROKE},
    "synthea_csv": {"csv/patients.csv": PATIENTS, "csv/encounters.csv": ENCOUNTERS},
}
