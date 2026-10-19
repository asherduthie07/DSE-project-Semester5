"""Access log excludes query strings, bodies and patient-entered features."""
from __future__ import annotations

import logging
from time import perf_counter

from fastapi import Request

logger = logging.getLogger("mediscope.api.access")


async def access_log(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = getattr(route, "path", "<unmatched>")
    logger.info("method=%s route=%s status=%s duration_ms=%.1f", request.method, path, response.status_code, (perf_counter() - start) * 1000)
    return response
