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
    conversions: int | None
    cost: int | None
    currency: str | None


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
    def fetch_metrics(self, date_from: date, date_to: date, connection_id: int | None = None) -> list[MetricRecord]:
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

    @abstractmethod
    def update_ad_link(self, ad_id: str | int, link_href: str) -> Dict[str, Any]:
        """
        Updates the link (href) of the ad in the external platform.
        """
        raise NotImplementedError
