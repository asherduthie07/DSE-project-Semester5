"""Stable public errors with no internal paths, credentials or feature values."""
from __future__ import annotations


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def missing(kind: str) -> APIError:
    return APIError(404, "NOT_FOUND", f"Unknown {kind}.")


def unavailable(kind: str) -> APIError:
    return APIError(503, "UNAVAILABLE", f"{kind} is unavailable; check local artifacts or service status.")
