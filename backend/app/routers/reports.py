from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.dependencies.services import get_services
from backend.app.services.container import Services

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def listing(services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.artifacts.listing()


@router.get("/{key}")
def report(key: str, services: Services = Depends(get_services)) -> dict[str, Any]:
    return services.artifacts.get(key)
