from __future__ import annotations

import csv
import time
import os
import hashlib
from datetime import date, timedelta
from typing import List, Dict, Any

import httpx
from pydantic import ValidationError

from app.connectors.base import AdsConnector, MetricRecord
from app.connectors.credentials import YandexCredentials
from app.core.config import get_settings
from app.db.models import MetricSnapshot, Platform


class YandexDirectConnector(AdsConnector):
    def __init__(self, credentials: Dict[str, Any] = None):
        self.credentials = credentials or {}
        self.token = self.credentials.get("token")
        self.login = self.credentials.get("login")
        self.is_mock = self._resolve_mock_mode()

    def credential_schema(self):
        return YandexCredentials

    def _resolve_mock_mode(self) -> bool:
        if os.getenv("YANDEX_DIRECT_MOCK", "0") == "1":
            return True
        if self.credentials.get("mock") is True:
            return True
        return not bool(self.token)

    def _mock_seed(self, connection_id: int | None) -> int:
        seed_input = f"yandex:{connection_id or 0}"
        digest = hashlib.sha256(seed_input.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    def _mock_campaign_ids(self, connection_id: int | None) -> list[str]:
        seed = self._mock_seed(connection_id)
        base = seed % 900
        return [str(1000 + base), str(2000 + base)]

    def validate_connection(self, credentials_json: dict) -> dict:
        payload = credentials_json or {}
        if payload.get("mock") is True or not payload.get("token"):
            return {"ok": True, "message": "Mock mode enabled"}
        try:
            self.credential_schema().model_validate(payload)
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

    def fetch_metrics(self, date_from: date, date_to: date, connection_id: int | None = None) -> list[MetricRecord]:
        if self.is_mock:
            campaign_ids = self._mock_campaign_ids(connection_id)
            results: list[MetricRecord] = []
            delta = date_to - date_from
            seed = self._mock_seed(connection_id)
            for i in range(delta.days + 1):
                current_date = date_from + timedelta(days=i)
                for cid in campaign_ids:
                    base = seed + int(cid)
                    impressions = 900 + base % 200 + i * 11
                    clicks = 40 + base % 25 + i * 2
                    spend = 120 + base % 80 + i * 5
                    purchases = (clicks // 10) or 1
                    revenue = spend * 3
                    results.append(
                        {
                            "date": current_date,
                            "platform": Platform.yandex,
                            "level": "campaign",
                            "campaign_external_id": str(cid),
                            "ad_group_external_id": None,
                            "ad_external_id": None,
                            "impressions": int(impressions),
                            "clicks": int(clicks),
                            "spend": int(spend),
                            "leads": int(clicks // 8),
                            "purchases": int(purchases),
                            "revenue": int(revenue),
                            "conversions": None,
                            "cost": int(spend),
                            "currency": "RUB",
                        }
                    )
            return results

        # Legacy method, kept for compatibility if needed, but we prefer get_daily_stats
        settings = get_settings()
        if not settings.yandex_reports_token:
            # Fallback to credentials if settings not present
            if not self.token:
                 raise ValueError("YANDEX reports token is not configured")
            token = self.token
        else:
            token = settings.yandex_reports_token

        report = self._fetch_report(
            settings.yandex_reports_url,
            token,
            date_from,
            date_to,
        )
        return [
            {
                "date": snap.date,
                "platform": Platform.yandex,
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
                "conversions": None,
                "cost": snap.spend,
                "currency": "RUB",
            }
            for snap in self._parse_tsv(report, skip_header=settings.yandex_reports_skip_header)
        ]

    def stop(self, external_ids: dict) -> None:
        return None

    def list_campaigns(self) -> List[Dict[str, Any]]:
        if self.is_mock:
            campaigns = self._mock_campaign_ids(None)
            return [
                {"id": campaigns[0], "name": "Mock Campaign 1", "status": "STARTED"},
                {"id": campaigns[1], "name": "Mock Campaign 2", "status": "STOPPED"},
            ]

        # TODO: Implement real API call using requests
        return []

    def get_daily_stats(self, campaign_ids: List[str], date_from: date, date_to: date) -> List[Dict[str, Any]]:
        if self.is_mock:
            results = []
            delta = date_to - date_from
            seed = self._mock_seed(None)
            for i in range(delta.days + 1):
                current_date = date_from + timedelta(days=i)
                for cid in campaign_ids:
                    base = seed + int(cid)
                    results.append({
                        "Date": current_date.isoformat(),
                        "CampaignId": cid,
                        "Impressions": 900 + base % 200 + i * 11,
                        "Clicks": 40 + base % 25 + i * 2,
                        "Cost": float(120 + base % 80 + i * 5)
                    })
            return results

        # Reuse existing logic but return raw dicts instead of MetricSnapshot objects
        # This allows the service layer to handle DB operations
        settings = get_settings()
        token = self.token or settings.yandex_reports_token
        if not token:
             raise ValueError("YANDEX reports token is not configured")

        report = self._fetch_report(
            settings.yandex_reports_url,
            token,
            date_from,
            date_to,
        )

        # Parse TSV to dicts
        rows = report.strip().splitlines()
        if settings.yandex_reports_skip_header and rows:
            rows = rows[1:]
        reader = csv.reader(rows, delimiter="\t")
        results = []
        for row in reader:
            if len(row) < 8:
                continue
            results.append({
                "Date": row[0],
                "CampaignId": row[1],
                "Clicks": int(row[2] or 0),
                "Impressions": int(row[3] or 0),
                "Cost": float(row[4] or 0),
                # Add other fields if needed
            })
        return results

    def _fetch_report(
        self,
        url: str,
        token: str,
        date_from: date,
        date_to: date,
    ) -> str:
        payload = {
            "params": {
                "SelectionCriteria": {
                    "DateFrom": date_from.isoformat(),
                    "DateTo": date_to.isoformat(),
                },
                "FieldNames": [
                    "Date",
                    "CampaignId",
                    "Clicks",
                    "Impressions",
                    "Cost",
                    "GoalsRoi",
                    "Conversions",
                    "Revenue",
                ],
                "ReportType": "CUSTOM_REPORT",
                "DateRangeType": "CUSTOM_DATE",
                "Format": "TSV",
                "IncludeVAT": "YES",
            }
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept-Language": "ru",
            "processingMode": "auto",
            "returnMoneyInMicros": "false",
        }

        backoff = 1.0
        max_retries = 5
        with httpx.Client(timeout=30) as client:
            for attempt in range(max_retries):
                response = client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.text
                if response.status_code in {201, 202, 429, 500, 502, 503, 504}:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                response.raise_for_status()
            response.raise_for_status()
        return ""

    def _parse_tsv(self, tsv_text: str, skip_header: bool) -> list[MetricSnapshot]:
        # Legacy helper for fetch_metrics
        rows = tsv_text.strip().splitlines()
        if skip_header and rows:
            rows = rows[1:]
        reader = csv.reader(rows, delimiter="\t")
        snapshots: list[MetricSnapshot] = []
        for row in reader:
            if len(row) < 8:
                continue
            date_value = datetime.strptime(row[0], "%Y-%m-%d").date()
            snapshots.append(
                MetricSnapshot(
                    date=date_value,
                    platform=Platform.yandex,
                    campaign_external_id=row[1],
                    clicks=int(row[2] or 0),
                    impressions=int(row[3] or 0),
                    spend=int(float(row[4] or 0)),
                    leads=int(float(row[6] or 0)),
                    purchases=0,
                    revenue=int(float(row[7] or 0)),
                )
            )
        return snapshots
