from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Any

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

    # New methods for sync pipeline
    @abstractmethod
    def list_campaigns(self) -> List[Dict[str, Any]]:
        """
        Returns list of campaigns:
        [{"id": "external_id", "name": "...", "status": "..."}]
        """
        raise NotImplementedError

    @abstractmethod
    def get_daily_stats(self, campaign_ids: List[str], date_from: date, date_to: date) -> List[Dict[str, Any]]:
        """
        Returns list of daily stats:
        [{"Date": "YYYY-MM-DD", "CampaignId": "...", "Impressions": int, "Clicks": int, "Cost": float}]
        """
        raise NotImplementedError
