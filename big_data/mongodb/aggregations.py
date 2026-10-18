"""Named MongoDB aggregations with explicit encounter versus patient denominators."""
from __future__ import annotations

from .connection import BigDataError

QUERIES = {
    "heart_classes": ("heart_disease_records", [{"$match": {"source_dataset": "heart"}}, {"$group": {"_id": "$heart_disease_binary", "count": {"$sum": 1}}}, {"$sort": {"_id": 1}}]),
    "diabetes_outcomes": ("diabetes_records", [{"$match": {"source_dataset": "diabetes"}}, {"$group": {"_id": "$class", "count": {"$sum": 1}}}, {"$sort": {"_id": 1}}]),
    "stroke_outcomes": ("stroke_records", [{"$match": {"source_dataset": "stroke"}}, {"$group": {"_id": "$stroke", "count": {"$sum": 1}}}, {"$sort": {"_id": 1}}]),
    "glucose_by_stroke": ("stroke_records", [{"$match": {"source_dataset": "stroke"}}, {"$group": {"_id": "$stroke", "average_glucose": {"$avg": "$avg_glucose_level"}, "records": {"$sum": 1}}}, {"$sort": {"_id": 1}}]),
    "patients_by_gender": ("hospital_patients", [{"$match": {"source_dataset": "patients"}}, {"$group": {"_id": "$GENDER", "patients": {"$sum": 1}}}, {"$sort": {"_id": 1}}]),
    "encounters_by_class": ("hospital_encounters", [{"$match": {"source_dataset": "encounters"}}, {"$group": {"_id": "$ENCOUNTERCLASS", "encounters": {"$sum": 1}}}, {"$sort": {"_id": 1}}]),
    "encounters_per_patient": ("hospital_encounters", [{"$match": {"source_dataset": "encounters"}}, {"$group": {"_id": "$PATIENT", "encounters": {"$sum": 1}}}, {"$sort": {"_id": 1}}]),
    "monthly_encounters": ("hospital_encounters", [{"$match": {"source_dataset": "encounters"}}, {"$group": {"_id": {"$substrBytes": ["$START", 0, 7]}, "encounters": {"$sum": 1}}}, {"$sort": {"_id": 1}}]),
}


def aggregate(db, query: str) -> list[dict]:
    if query not in QUERIES:
        raise BigDataError(f"Unknown aggregation {query}; choose {list(QUERIES)}")
    collection, pipeline = QUERIES[query]
    return list(db[collection].aggregate(pipeline))


def reconcile(db) -> dict[str, dict]:
    """Compare every live aggregation with the identical Phase I source rows."""
    from .import_data import read_source

    heart, _ = read_source("heart")
    diabetes, _ = read_source("diabetes")
    stroke, _ = read_source("stroke")
    patients, _ = read_source("patients")
    encounters, _ = read_source("encounters")
    expected = {
        "heart_classes": heart["heart_disease_binary"].value_counts().to_dict(),
        "diabetes_outcomes": diabetes["class"].value_counts().to_dict(),
        "stroke_outcomes": stroke["stroke"].value_counts().to_dict(),
        "patients_by_gender": patients["GENDER"].value_counts().to_dict(),
        "encounters_by_class": encounters["ENCOUNTERCLASS"].value_counts().to_dict(),
        "encounters_per_patient": encounters["PATIENT"].value_counts().to_dict(),
        "monthly_encounters": encounters["START"].str.slice(0, 7).value_counts().to_dict(),
    }
    results = {}
    for query, reference in expected.items():
        rows = aggregate(db, query)
        field = "patients" if query == "patients_by_gender" else "encounters" if query.startswith("encounters") or query == "monthly_encounters" else "count"
        actual = {row["_id"]: row[field] for row in rows}
        results[query] = {"match": actual == reference, "groups": len(actual), "total": sum(actual.values())}
    glucose = aggregate(db, "glucose_by_stroke")
    means = stroke.groupby("stroke")["avg_glucose_level"].mean().to_dict()
    results["glucose_by_stroke"] = {"match": all(abs(row["average_glucose"] - means[row["_id"]]) < 1e-8 for row in glucose) and len(glucose) == len(means), "groups": len(glucose)}
    if not all(item["match"] for item in results.values()):
        raise BigDataError(f"MongoDB aggregation mismatch: {results}")
    return results


def crud_demo(db) -> dict:
    """Run all CRUD operations on one isolated demonstration document."""
    collection = db.phase5_demo
    key = "phase5-controlled-demo"
    collection.delete_one({"_id": key, "demo": True})
    collection.insert_one({"_id": key, "demo": True, "label": "created", "order": 1})
    read = collection.find_one({"_id": key})["label"]
    collection.update_one({"_id": key, "demo": True}, {"$set": {"label": "updated"}})
    filtered = [doc["label"] for doc in collection.find({"demo": True}, {"label": 1}).sort("order", 1)]
    deleted = collection.delete_one({"_id": key, "demo": True}).deleted_count
    return {"create": True, "read": read, "update": filtered, "delete_count": deleted}
