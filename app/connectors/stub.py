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
