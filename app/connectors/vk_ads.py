from __future__ import annotations

from datetime import date

from app.connectors.base import AdsConnector
from app.connectors.vk_ads_client import VkAdsClient
from app.db.models import MetricSnapshot, Platform


class VkAdsConnector(AdsConnector):
    def __init__(self, credentials_json: dict | None = None) -> None:
        self._credentials = credentials_json

    def validate_connection(self, credentials_json: dict) -> bool:
        access_token = credentials_json.get("access_token")
        version = credentials_json.get("version")
        return bool(access_token and version)

    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        return {"campaign_id": "stub"}

    def sync_status(self, external_ids: dict) -> dict:
        return {"campaign_id": "active"}

    def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricSnapshot]:
        client = self._build_client(self._credentials)
        if not self._credentials:
            raise ValueError("Missing VK credentials")
        account_id = self._credentials.get("account_id")
        ids = self._credentials.get("ids", [])
        ids_type = self._credentials.get("ids_type", "campaign")
        if not account_id or not ids:
            raise ValueError("Missing VK metrics parameters")
        response = client.get_statistics(
            account_id=int(account_id),
            ids=ids,
            ids_type=ids_type,
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
            period="day",
        )
        return self._parse_metrics_response(response)

    def stop(self, external_ids: dict) -> None:
        return None

    def fetch_raw(self, method_name: str, credentials_json: dict, params: dict | None = None) -> dict:
        client = self._build_client(credentials_json)
        return client.call(method_name, params or {})

    def _build_client(self, credentials_json: dict | None = None) -> VkAdsClient:
        if credentials_json is None:
            raise ValueError("Credentials required")
        access_token = credentials_json.get("access_token")
        version = credentials_json.get("version")
        if not access_token or not version:
            raise ValueError("Missing VK credentials")
        return VkAdsClient(access_token=access_token, version=version)

    @staticmethod
    def _parse_metrics_response(payload: dict) -> list[MetricSnapshot]:
        snapshots: list[MetricSnapshot] = []
        for entry in payload.get("response", []):
            for stat in entry.get("stats", []):
                snapshots.append(
                    MetricSnapshot(
                        date=date.fromisoformat(stat.get("day")),
                        platform=Platform.vk,
                        campaign_external_id=str(entry.get("id", "")),
                        clicks=int(stat.get("clicks") or 0),
                        impressions=int(stat.get("impressions") or 0),
                        spend=int(float(stat.get("spent") or 0)),
                        leads=0,
                        purchases=0,
                        revenue=0,
                    )
                )
        return snapshots
