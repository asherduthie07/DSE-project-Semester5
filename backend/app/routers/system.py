from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.dependencies.services import get_services
from backend.app.schemas.api import Health, Readiness
from backend.app.services.container import Services

router = APIRouter(tags=["system"])


@router.get("/health", response_model=Health)
def health() -> Health:
    return Health()


@router.get("/system/readiness", response_model=Readiness)
def readiness(services: Services = Depends(get_services)) -> Readiness:
    return services.readiness()
