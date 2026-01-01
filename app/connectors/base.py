from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.db.models import MetricSnapshot


class AdsConnector(ABC):
    @abstractmethod
    def validate_connection(self, credentials_json: dict) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        raise NotImplementedError

    @abstractmethod
    def sync_status(self, external_ids: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def stop(self, external_ids: dict) -> None:
        raise NotImplementedError
