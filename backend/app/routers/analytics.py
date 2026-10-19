from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.dependencies.services import get_services
from backend.app.schemas.api import ChartResponse
from backend.app.services.container import Services

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/{dataset}/overview")
def overview(dataset: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.analytics.overview(dataset)


@router.get("/{dataset}/distributions")
def distributions(dataset: str, table: str | None = None, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.analytics.distributions(dataset, table)


@router.get("/{dataset}/correlations")
def correlations(dataset: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.analytics.correlations(dataset)


@router.get("/{dataset}/hypotheses")
def hypotheses(dataset: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.analytics.hypotheses(dataset)


@router.get("/{dataset}/charts", response_model=ChartResponse)
def charts(dataset: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.analytics.charts(dataset)
