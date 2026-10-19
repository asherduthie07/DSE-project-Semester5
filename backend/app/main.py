"""MediScope AI versioned, research-only FastAPI application."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import Settings
from backend.app.core.errors import APIError
from backend.app.middleware.access import access_log
from backend.app.routers import analytics, bigdata, datasets, models, predictions, reports, system
from backend.app.services.container import Services

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("mediscope.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        services = Services(config)
        services.initialize()
        app.state.services = services
        try:
            yield
        finally:
            services.close()

    app = FastAPI(title="MediScope AI Research API", version="1.0.0", lifespan=lifespan,
                  description="Research and educational data, analytics and prediction API. No clinical validation or medical advice.")
    app.add_middleware(CORSMiddleware, allow_origins=list(config.cors_origins), allow_credentials=False,
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
    app.middleware("http")(access_log)
    for router in (system.router, datasets.router, analytics.router, models.router, predictions.router, bigdata.router, reports.router):
        app.include_router(router, prefix="/api/v1")

    @app.exception_handler(APIError)
    async def api_error(_request: Request, exc: APIError):
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, _exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"error": {"code": "INVALID_REQUEST", "message": "Request validation failed; consult the OpenAPI schema."}})

    @app.exception_handler(Exception)
    async def internal_error(_request: Request, exc: Exception):
        logger.error("Unhandled backend error type=%s", type(exc).__name__)
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "The request could not be completed."}})

    return app


app = create_app()
