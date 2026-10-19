from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from backend.app.dependencies.services import get_services
from backend.app.schemas.api import DatasetList, DatasetSchema, DatasetSummary, RecordPage
from backend.app.services.container import Services

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=DatasetList)
def listing(services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.datasets.listing()


@router.get("/{dataset_id}/schema", response_model=DatasetSchema)
def schema(dataset_id: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.datasets.schema(dataset_id)


@router.get("/{dataset_id}/summary", response_model=DatasetSummary)
def summary(dataset_id: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.datasets.summary(dataset_id)


@router.get("/{dataset_id}/quality")
def quality(dataset_id: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.datasets.quality(dataset_id)


@router.get("/{dataset_id}/records", response_model=RecordPage)
def records(dataset_id: str, table: str | None = None, offset: int = Query(0, ge=0, le=100000),
            limit: int = Query(20, ge=1, le=100), filter_field: str | None = None,
            filter_value: str | None = None, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.datasets.records(dataset_id, table, offset, limit, filter_field, filter_value)
