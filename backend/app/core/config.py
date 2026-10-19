"""Server-owned configuration; no request may choose a project path or service URI."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    mongo_uri: str
    cors_origins: tuple[str, ...]
    hdfs_url: str
    yarn_url: str

    @classmethod
    def from_env(cls) -> Settings:
        root = Path(__file__).resolve().parents[3]
        origins = os.environ.get(
            "MEDISCOPE_CORS_ORIGINS",
            "http://127.0.0.1:4200,http://localhost:4200,http://127.0.0.1:5173,http://localhost:5173",
        )
        return cls(
            project_root=root,
            mongo_uri=os.environ.get("MEDISCOPE_MONGO_URI", "mongodb://127.0.0.1:27017"),
            cors_origins=tuple(x.strip() for x in origins.split(",") if x.strip()),
            hdfs_url=os.environ.get("MEDISCOPE_HDFS_URL", "http://127.0.0.1:9870").rstrip("/"),
            yarn_url=os.environ.get("MEDISCOPE_YARN_URL", "http://127.0.0.1:8088").rstrip("/"),
        )
