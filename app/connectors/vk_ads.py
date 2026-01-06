from __future__ import annotations

import os
from datetime import date, timedelta

from pydantic import ValidationError

from app.connectors.base import AdsConnector, MetricRecord
from app.connectors.credentials import VkCredentials
from app.connectors.vk_ads_client import VkAdsClient
from app.db.models import MetricSnapshot, Platform


class VkAdsConnector(AdsConnector):
    def __init__(self, credentials_json: dict | None = None) -> None:
        self._credentials = credentials_json
        self.is_mock = os.getenv("VK_ADS_MOCK", "0") == "1"

    def credential_schema(self):
        return VkCredentials

    def validate_connection(self, credentials_json: dict) -> dict:
        try:
            self.credential_schema().model_validate(credentials_json)
        except ValidationError as exc:
            return {
                "ok": False,
                "error_code": "invalid_credentials",
                "message": exc.errors()[0]["msg"],
            }
        return {"ok": True}

    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        return {"campaign_id": "stub"}

    def sync_status(self, external_ids: dict) -> dict:
        return {"campaign_id": "active"}

    def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricRecord]:
        if self.is_mock:
            campaigns = self.list_campaigns()
            campaign_ids = [str(camp["id"]) for camp in campaigns]
            rows = self.get_daily_stats(campaign_ids, date_from, date_to)
            return [
                {
                    "date": date.fromisoformat(row["Date"]),
                    "platform": Platform.vk,
                    "level": "campaign",
                    "campaign_external_id": str(row["CampaignId"]),
                    "ad_group_external_id": None,
                    "ad_external_id": None,
                    "impressions": int(row.get("Impressions") or 0),
                    "clicks": int(row.get("Clicks") or 0),
                    "spend": int(float(row.get("Cost") or 0)),
                    "leads": 0,
                    "purchases": 0,
                    "revenue": 0,
                }
                for row in rows
            ]

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
        return [
            {
                "date": snap.date,
                "platform": snap.platform,
                "level": "campaign",
                "campaign_external_id": snap.campaign_external_id,
                "ad_group_external_id": None,
                "ad_external_id": None,
                "impressions": snap.impressions,
                "clicks": snap.clicks,
                "spend": snap.spend,
                "leads": snap.leads,
                "purchases": snap.purchases,
                "revenue": snap.revenue,
            }
            for snap in self._parse_metrics_response(response)
        ]

    def stop(self, external_ids: dict) -> None:
        return None

    def list_campaigns(self):
        if self.is_mock:
            return [
                {"id": "vk_111", "name": "VK Mock 1", "status": "ACTIVE"},
                {"id": "vk_222", "name": "VK Mock 2", "status": "PAUSED"},
            ]
        raise NotImplementedError("VK list_campaigns not implemented yet")

    def get_daily_stats(self, campaign_ids, date_from: date, date_to: date):
        if self.is_mock:
            results = []
            delta = date_to - date_from
            for i in range(delta.days + 1):
                current_date = date_from + timedelta(days=i)
                for cid in campaign_ids:
                    results.append(
                        {
                            "Date": current_date.isoformat(),
                            "CampaignId": cid,
                            "Impressions": 200,
                            "Clicks": 20,
                            "Cost": 400.0,
                        }
                    )
            return results
        raise NotImplementedError("VK get_daily_stats not implemented yet")

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
