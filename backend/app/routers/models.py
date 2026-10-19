from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.dependencies.services import get_services
from backend.app.schemas.api import ModelDetail, ModelList
from backend.app.services.container import Services

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=ModelList)
def listing(services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.models.listing()


@router.get("/{task}", response_model=ModelDetail)
def detail(task: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.models.detail(task)


@router.get("/{task}/comparison")
def comparison(task: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.models.comparison(task)


@router.get("/{task}/confusion-matrices")
def matrices(task: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.models.matrices(task)


@router.get("/{task}/curves")
def curves(task: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.models.curves(task)


@router.get("/{task}/explanations")
def explanations(task: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.models.explanations(task)
