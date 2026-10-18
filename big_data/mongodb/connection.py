"""Explicit, bounded MongoDB connection handling."""
from __future__ import annotations

import os

from pymongo import MongoClient
from pymongo.errors import PyMongoError

DATABASE = "mediscope_healthcare"


class BigDataError(RuntimeError):
    """A Phase V prerequisite or validation failed."""


def connect():
    uri = os.environ.get("MEDISCOPE_MONGO_URI", "mongodb://127.0.0.1:27017")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
        client.admin.command("ping")
    except PyMongoError as exc:
        raise BigDataError(f"MongoDB unavailable at {uri.split('@')[-1]}: {exc.__class__.__name__}: {exc}") from exc
    return client
