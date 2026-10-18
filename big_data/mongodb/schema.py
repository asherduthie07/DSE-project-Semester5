"""Phase V collection contract. Source columns retain their prepared CSV names."""
from __future__ import annotations

from pymongo import ASCENDING

COLLECTIONS = {
    "heart": ("heart_disease_records", "heart.csv", 303, "heart_disease_binary"),
    "diabetes": ("diabetes_records", "diabetes.csv", 520, "class"),
    "stroke": ("stroke_records", "stroke.csv", 5110, "stroke"),
    "patients": ("hospital_patients", "synthea_patients.csv", 1171, None),
    "encounters": ("hospital_encounters", "synthea_encounters.csv", 53346, None),
}
PATIENT_FIELDS = ("Id", "BIRTHDATE", "DEATHDATE", "MARITAL", "RACE", "ETHNICITY", "GENDER", "HEALTHCARE_EXPENSES", "HEALTHCARE_COVERAGE")
ENCOUNTER_FIELDS = ("Id", "START", "STOP", "PATIENT", "ENCOUNTERCLASS", "CODE", "DESCRIPTION", "BASE_ENCOUNTER_COST", "TOTAL_CLAIM_COST", "PAYER_COVERAGE", "REASONCODE", "REASONDESCRIPTION")
INDEXES = {
    "heart_disease_records": [("heart_disease_binary", ASCENDING)],
    "diabetes_records": [("class", ASCENDING)],
    "stroke_records": [("stroke", ASCENDING)],
    "hospital_patients": [("GENDER", ASCENDING), ("RACE", ASCENDING)],
    "hospital_encounters": [("PATIENT", ASCENDING), ("ENCOUNTERCLASS", ASCENDING), ("START", ASCENDING)],
}


def create_indexes(db) -> dict[str, list[str]]:
    result = {}
    for collection, specs in INDEXES.items():
        result[collection] = [db[collection].create_index([spec]) for spec in specs]
    return result
