from __future__ import annotations

import csv
import time
import os
from datetime import date, datetime, timedelta
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
        self.is_mock = os.getenv("YANDEX_DIRECT_MOCK", "0") == "1"

    def credential_schema(self):
        return YandexCredentials

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
                    "platform": Platform.yandex,
                    "level": "campaign",
                    "campaign_external_id": str(row["CampaignId"]),
                    "ad_group_external_id": None,
                    "ad_external_id": None,
                    "impressions": int(row.get("Impressions") or 0),
                    "clicks": int(row.get("Clicks") or 0),
                    "spend": int(float(row.get("Cost") or 0)),
                    "leads": int(float(row.get("Leads") or 0)),
                    "purchases": int(float(row.get("Purchases") or 0)),
                    "revenue": int(float(row.get("Revenue") or 0)),
                }
                for row in rows
            ]

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
            }
            for snap in self._parse_tsv(report, skip_header=settings.yandex_reports_skip_header)
        ]

    def stop(self, external_ids: dict) -> None:
        return None

    def list_campaigns(self) -> List[Dict[str, Any]]:
        if self.is_mock:
            return [
                {"id": "111", "name": "Mock Campaign 1", "status": "STARTED"},
                {"id": "222", "name": "Mock Campaign 2", "status": "STOPPED"},
            ]

        # TODO: Implement real API call using requests
        return []

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
                        "Impressions": 100 + int(cid),
                        "Clicks": 10 + int(cid),
                        "Cost": 500.0
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
