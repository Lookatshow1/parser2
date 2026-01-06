from datetime import timedelta
from typing import Any

from app.connectors.base import AdsConnector, MetricRecord
from app.db.models import Platform


class StubConnector(AdsConnector):
    def __init__(self, credentials: dict | None = None):
        self.credentials = credentials or {}

    def validate_connection(self, credentials_json: dict) -> dict:
        return {"ok": True}

    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        return {"campaign_id": "stub"}

    def sync_status(self, external_ids: dict) -> dict:
        return {"campaign_id": "active"}

    def fetch_metrics(self, date_from, date_to) -> list[MetricRecord]:
        results: list[MetricRecord] = []
        campaigns = self.list_campaigns()
        current = date_from
        while current <= date_to:
            for camp in campaigns:
                results.append(
                    {
                        "date": current,
                        "platform": Platform.stub,
                        "level": "campaign",
                        "campaign_external_id": str(camp["id"]),
                        "ad_group_external_id": None,
                        "ad_external_id": None,
                        "impressions": 100,
                        "clicks": 10,
                        "spend": 250,
                        "leads": 0,
                        "purchases": 0,
                        "revenue": 0,
                    }
                )
            current = current + timedelta(days=1)
        return results

    def stop(self, external_ids: dict) -> None:
        return None

    def list_campaigns(self) -> list[dict[str, Any]]:
        return [
            {"id": "stub_1", "name": "Stub Campaign 1", "status": "ACTIVE"},
            {"id": "stub_2", "name": "Stub Campaign 2", "status": "PAUSED"},
        ]

    def get_daily_stats(self, campaign_ids, date_from, date_to):
        results = []
        current = date_from
        while current <= date_to:
            for cid in campaign_ids:
                results.append(
                    {
                        "Date": current.isoformat(),
                        "CampaignId": cid,
                        "Impressions": 100,
                        "Clicks": 10,
                        "Cost": 250.0,
                    }
                )
            current = current + timedelta(days=1)
        return results

    def fetch_raw(self, method: str, params: dict | None = None) -> dict:
        return {"ok": True, "method": method, "params": params or {}}
