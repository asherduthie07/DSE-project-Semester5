from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.dependencies.services import get_services
from backend.app.schemas.api import AggregationResult, BigDataStatus, CollectionCounts
from backend.app.services.container import Services

router = APIRouter(prefix="/bigdata", tags=["bigdata"])


@router.get("/status", response_model=BigDataStatus)
def status(services: Services = Depends(get_services)) -> dict[str, Any]:
    return {"live": services.bigdata.live_status(), "saved_mapreduce_evidence": services.bigdata.evidence()}


@router.get("/collections", response_model=CollectionCounts)
def collections(services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.bigdata.collections()


@router.get("/aggregations", response_model=AggregationResult)
def aggregation(query: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.bigdata.aggregation(query)


@router.get("/mapreduce/jobs")
def jobs(services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.bigdata.jobs()


@router.get("/mapreduce/results")
def results(services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.bigdata.results()
