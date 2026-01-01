from __future__ import annotations

import csv
import logging
import time
from datetime import date, datetime

import httpx

from app.db.models import MetricSnapshot, Platform

logger = logging.getLogger(__name__)


class YandexReportsError(RuntimeError):
    pass


class YandexDirectReportsClient:
    def __init__(
        self,
        token: str,
        client_login: str | None = None,
        base_url: str = "https://api.direct.yandex.com/v5/reports",
        rate_limit_sleep: float = 1.0,
    ) -> None:
        self._token = token
        self._client_login = client_login
        self._base_url = base_url
        self._rate_limit_sleep = rate_limit_sleep

    def fetch_report(
        self,
        date_from: date,
        date_to: date,
        granularity: str,
        skip_report_header: bool,
        skip_column_header: bool,
        skip_report_summary: bool,
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
                    "Impressions",
                    "Clicks",
                    "Cost",
                ],
                "ReportType": "CUSTOM_REPORT",
                "DateRangeType": "CUSTOM_DATE",
                "Format": "TSV",
                "ReportName": "Metrics",
                "IncludeVAT": "YES",
                "IncludeDiscount": "YES",
                "Granularity": granularity,
            }
        }
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept-Language": "ru",
            "processingMode": "auto",
            "skipReportHeader": "true" if skip_report_header else "false",
            "skipColumnHeader": "true" if skip_column_header else "false",
            "skipReportSummary": "true" if skip_report_summary else "false",
        }
        if self._client_login:
            headers["Client-Login"] = self._client_login

        backoff = 1.0
        max_retries = 5
        with httpx.Client(timeout=30) as client:
            for _ in range(max_retries):
                response = client.post(self._base_url, json=payload, headers=headers)
                request_id = response.headers.get("RequestId")
                if response.status_code == 200:
                    return response.text
                if response.status_code in {201, 202}:
                    retry_in = int(response.headers.get("retryIn", "5"))
                    time.sleep(retry_in)
                    continue
                if response.status_code in {400, 500, 502}:
                    logger.error("Yandex Reports error status=%s request_id=%s", response.status_code, request_id)
                    raise YandexReportsError(f"Reports error {response.status_code} request_id={request_id}")
                time.sleep(backoff)
                backoff *= 2
                time.sleep(self._rate_limit_sleep)
            raise YandexReportsError("Reports request failed after retries")


def parse_tsv_metrics(tsv_text: str, skip_header: bool = False) -> list[MetricSnapshot]:
    rows = tsv_text.strip().splitlines()
    if skip_header and rows:
        rows = rows[1:]
    reader = csv.reader(rows, delimiter="\t")
    snapshots: list[MetricSnapshot] = []
    for row in reader:
        if len(row) < 5:
            continue
        date_value = datetime.strptime(row[0], "%Y-%m-%d").date()
        campaign_id = row[1] if row[1] else ""
        snapshots.append(
            MetricSnapshot(
                date=date_value,
                platform=Platform.yandex,
                campaign_external_id=campaign_id,
                impressions=int(row[2] or 0),
                clicks=int(row[3] or 0),
                spend=int(float(row[4] or 0)),
                leads=0,
                purchases=0,
                revenue=0,
            )
        )
    return snapshots
