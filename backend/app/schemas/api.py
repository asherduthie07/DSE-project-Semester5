from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr


class State(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_VERIFIED = "NOT_VERIFIED"


class Component(BaseModel):
    status: State
    message: str


class Readiness(BaseModel):
    status: State
    components: dict[str, Component]


class Health(BaseModel):
    status: State = State.READY
    service: str = "mediscope-api"


class DatasetMetadata(BaseModel):
    id: str
    name: str
    records: str
    source_url: str
    source_sha256: str
    tables: dict[str, int]


class DatasetList(BaseModel):
    datasets: list[DatasetMetadata]


class DatasetSchema(BaseModel):
    dataset_id: str
    name: str
    source_sha256: str
    tables: dict[str, dict[str, Any]]


class DatasetSummary(BaseModel):
    dataset_id: str
    name: str
    source_url: str
    provenance: str
    source_sha256: str
    tables: dict[str, dict[str, Any]]
    rows: dict[str, int]


class RecordPage(BaseModel):
    dataset_id: str
    table: str
    source_rows: int
    total: int
    offset: int
    limit: int
    items: list[dict[str, Any]]


class ChartSeries(BaseModel):
    id: str
    label: str
    categories: list[str]
    values: list[int]
    unit: str
    sample_size: int
    missingness_note: str


class ChartResponse(BaseModel):
    dataset_id: str
    charts: list[ChartSeries]
    approved_figures: list[str]
    source_url: str
    caveat: str


class ModelTaskSummary(BaseModel):
    task: str
    selected_model: str
    artifact_version: str
    available_for_prediction: bool


class ModelList(BaseModel):
    tasks: list[ModelTaskSummary]
    warning: str


class ModelDetail(BaseModel):
    task: str
    selected_model: str
    artifact_version: str
    artifact_sha256: str
    dataset_id: str
    feature_columns: list[str]
    cv_strategy: str
    selection_score: str
    selection_reason: str
    split_sha256: str
    prepared_sha256: str
    available_for_prediction: bool
    warning: str


class BigDataStatus(BaseModel):
    live: dict[str, Component]
    saved_mapreduce_evidence: dict[str, Any]


class CollectionCounts(BaseModel):
    status: State
    database: str
    counts: dict[str, int]
    source_counts_match: bool


class AggregationResult(BaseModel):
    query: str
    collection: str
    rows: list[dict[str, Any]]
    denominator: str


FeatureValue = StrictBool | StrictInt | StrictFloat | StrictStr | None


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: dict[str, FeatureValue] = Field(min_length=1)


class PredictionResponse(BaseModel):
    task: str
    predicted_class: int
    predicted_source_label: str | int
    estimated_model_score: float
    model_name: str
    model_version: str
    model_sha256: str
    decision_threshold: float
    explanation: dict[str, Any]
    warning: str
