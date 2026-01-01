from __future__ import annotations

import csv
import time
from datetime import date, datetime

import httpx

from app.connectors.base import AdsConnector
from app.core.config import get_settings
from app.db.models import MetricSnapshot, Platform


class YandexDirectConnector(AdsConnector):
    def validate_connection(self, credentials_json: dict) -> bool:
        return True

    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        return {"campaign_id": "stub"}

    def sync_status(self, external_ids: dict) -> dict:
        return {"campaign_id": "active"}

    def fetch_metrics(self, date_from: date, date_to: date) -> list[MetricSnapshot]:
        settings = get_settings()
        if not settings.yandex_reports_token:
            raise ValueError("YANDEX reports token is not configured")

        report = self._fetch_report(
            settings.yandex_reports_url,
            settings.yandex_reports_token,
            date_from,
            date_to,
        )
        return self._parse_tsv(report, skip_header=settings.yandex_reports_skip_header)

    def stop(self, external_ids: dict) -> None:
        return None

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
