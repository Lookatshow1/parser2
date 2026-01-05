from datetime import timedelta

from app.connectors.base import AdsConnector


class StubConnector(AdsConnector):
    def validate_connection(self, credentials_json: dict) -> bool:
        return True

    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        return {"campaign_id": "stub"}

    def sync_status(self, external_ids: dict) -> dict:
        return {"campaign_id": "active"}

    def fetch_metrics(self, date_from, date_to):
        return []

    def stop(self, external_ids: dict) -> None:
        return None

    def list_campaigns(self):
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
