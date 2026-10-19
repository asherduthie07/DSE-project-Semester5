from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.dependencies.services import get_services
from backend.app.schemas.api import PredictionRequest, PredictionResponse
from backend.app.services.container import Services

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{task}/schema")
def schema(task: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.models.input_schema(task)


@router.post("/{task}", response_model=PredictionResponse)
def predict(task: str, request: PredictionRequest, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.models.predict(task, request.features)
