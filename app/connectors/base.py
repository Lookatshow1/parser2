from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Any, TypedDict

from pydantic import BaseModel

from app.db.models import MetricSnapshot, Platform


class MetricRecord(TypedDict):
    date: date
    platform: Platform
    level: str
    campaign_external_id: str
    ad_group_external_id: str | None
    ad_external_id: str | None
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int


class AdsConnector(ABC):
    @abstractmethod
    def credential_schema(self) -> type[BaseModel]:
        raise NotImplementedError

    @abstractmethod
    def validate_connection(self, credentials_json: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        raise NotImplementedError

    @abstractmethod
    def sync_status(self, external_ids: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricRecord]:
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
