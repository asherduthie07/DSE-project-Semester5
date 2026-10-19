"""Application-scoped service lifecycle and readiness aggregation."""
from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.schemas.api import Component, Readiness, State
from backend.app.services.analytics import AnalyticsService
from backend.app.services.artifacts import ArtifactService
from backend.app.services.bigdata import BigDataService
from backend.app.services.datasets import DatasetService, TABLE_KEYS
from backend.app.services.models import ModelService


class Services:
    def __init__(self, settings: Settings) -> None:
        self.datasets = DatasetService(settings.project_root)
        self.analytics = AnalyticsService(settings.project_root, self.datasets)
        self.models = ModelService(settings.project_root)
        self.bigdata = BigDataService(settings, self.datasets)
        self.artifacts = ArtifactService(settings.project_root)

    def initialize(self) -> None:
        self.models.initialize()

    def close(self) -> None:
        self.bigdata.close()
        self.datasets.load.cache_clear()
        self.analytics.report.cache_clear()
        self.models.loaded.clear()

    def readiness(self) -> Readiness:
        components = {"api": Component(status=State.READY, message="API process is serving requests.")}
        try:
            self.datasets.listing()
            components["datasets"] = Component(status=State.READY, message="All five prepared tables passed Phase I checks.")
        except Exception:
            components["datasets"] = Component(status=State.UNAVAILABLE, message="A prepared dataset is missing or failed verification.")
        try:
            for dataset in TABLE_KEYS:
                self.analytics.report(dataset)
            components["eda_reports"] = Component(status=State.READY, message="Phase II reports match prepared source hashes.")
        except Exception:
            components["eda_reports"] = Component(status=State.UNAVAILABLE, message="A Phase II report is missing or failed verification.")
        available = len(self.models.loaded)
        components["trained_models"] = Component(status=State.READY if available == 3 else State.DEGRADED if available else State.UNAVAILABLE,
                                                   message=f"{available} of 3 selected trusted model artifacts loaded.")
        live = self.bigdata.live_status()
        for key in ("mongodb", "hdfs", "yarn"):
            components[key] = Component(**live[key])
        evidence = self.bigdata.evidence()
        components["hadoop_job_evidence"] = Component(status=State(evidence["status"]),
                    message="Saved YARN job and reducer output reconcile with Phase I encounters." if evidence["status"] == "READY" else evidence["message"])
        powerbi = self.artifacts.listing()["powerbi"]
        components["powerbi"] = Component(status=State.DEGRADED if powerbi["static_artifacts"] else State.NOT_VERIFIED,
                   message="Static exports available; Desktop and Service runtime not verified." if powerbi["static_artifacts"] else "Power BI artifacts are unavailable.")
        core = ("datasets", "eda_reports", "trained_models")
        overall = State.UNAVAILABLE if any(components[k].status == State.UNAVAILABLE for k in core) else State.DEGRADED if any(c.status != State.READY for c in components.values()) else State.READY
        return Readiness(status=overall, components=components)
