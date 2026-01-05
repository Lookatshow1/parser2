from __future__ import annotations

import os
from datetime import date, timedelta
from typing import List, Dict, Any

from app.connectors.base import AdsConnector
from app.db.models import MetricSnapshot


class OzonPerformanceConnector(AdsConnector):
    def __init__(self, credentials: Dict[str, Any] = None):
        self.credentials = credentials or {}
        self.client_id = self.credentials.get("client_id")
        self.client_secret = self.credentials.get("client_secret")
        self.is_mock = os.getenv("OZON_PERF_MOCK", "0") == "1"

    def validate_connection(self, credentials_json: dict) -> bool:
        return True

    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        return {"campaign_id": "stub_ozon"}

    def sync_status(self, external_ids: dict) -> dict:
        return {"campaign_id": "active"}

    def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricSnapshot]:
        # Not implemented for legacy flow
        return []

    def stop(self, external_ids: dict) -> None:
        return None

    def list_campaigns(self) -> List[Dict[str, Any]]:
        if self.is_mock:
            return [
                {"id": "ozon_aaa", "name": "Ozon Campaign A", "status": "ACTIVATED"},
                {"id": "ozon_bbb", "name": "Ozon Campaign B", "status": "PAUSED"},
            ]

        # TODO: Implement real API call
        raise NotImplementedError("Ozon real API not implemented yet")

    def get_daily_stats(self, campaign_ids: List[str], date_from: date, date_to: date) -> List[Dict[str, Any]]:
        if self.is_mock:
            results = []
            delta = date_to - date_from
            for i in range(delta.days + 1):
                current_date = date_from + timedelta(days=i)
                for cid in campaign_ids:
                    results.append({
                        "Date": current_date.isoformat(),
                        "CampaignId": cid,
                        "Impressions": 500 + (10 if cid == "ozon_aaa" else 20),
                        "Clicks": 50 + (1 if cid == "ozon_aaa" else 2),
                        "Cost": 1000.0
                    })
            return results

        # TODO: Implement real API call
        raise NotImplementedError("Ozon real API not implemented yet")
