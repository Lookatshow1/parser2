from __future__ import annotations

from datetime import date

import httpx

from app.connectors.base import AdsConnector
from app.db.models import MetricSnapshot


class OzonPerformanceConnector(AdsConnector):
    def validate_connection(self, credentials_json: dict) -> bool:
        client_id = credentials_json.get("client_id")
        api_key = credentials_json.get("api_key")
        if not client_id or not api_key:
            return False
        self._test_request_stub(client_id, api_key)
        return True

    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        return {"campaign_id": "stub"}

    def sync_status(self, external_ids: dict) -> dict:
        return {"campaign_id": "active"}

    def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricSnapshot]:
        return []

    def stop(self, external_ids: dict) -> None:
        return None

    @staticmethod
    def _test_request_stub(client_id: str, api_key: str) -> None:
        with httpx.Client(timeout=5) as client:
            client.headers.update({"Client-Id": client_id, "Api-Key": api_key})
