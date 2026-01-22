from __future__ import annotations

import os
import asyncio
from datetime import date, timedelta, datetime
from typing import List, Dict, Any

from pydantic import ValidationError

from app.connectors.base import AdsConnector, MetricRecord
from app.connectors.credentials import OzonCredentials
from app.db.models import MetricSnapshot, Platform
from app.services.oauth.base import OzonOAuth
from app.services.platforms.ozon_perf import OzonPerformanceClient


class OzonPerformanceConnector(AdsConnector):
    def __init__(self, credentials: Dict[str, Any] = None):
        self.credentials = credentials or {}
        self.client_id = self.credentials.get("client_id")
        self.client_secret = self.credentials.get("client_secret")
        self.is_mock = os.getenv("OZON_PERF_MOCK", "0") == "1"
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

    def _get_access_token(self) -> str:
        if self._access_token and self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return self._access_token
        if not self.client_id or not self.client_secret:
            raise ValueError("Ozon credentials are missing")

        async def _fetch() -> str:
            oauth = OzonOAuth(client_id=self.client_id, client_secret=self.client_secret, redirect_uri="")
            token = await oauth.exchange_code("")
            await oauth.close()
            self._access_token = token.access_token
            self._token_expires_at = token.expires_at
            return token.access_token

        return asyncio.run(_fetch())

    def _build_client(self) -> OzonPerformanceClient:
        token = self._get_access_token()
        return OzonPerformanceClient(token)

    def credential_schema(self):
        return OzonCredentials

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
        return {"campaign_id": "stub_ozon"}

    def sync_status(self, external_ids: dict) -> dict:
        return {"campaign_id": "active"}

    def fetch_metrics(self, date_from: date, date_to: date, connection_id: int | None = None) -> list[MetricRecord]:
        if self.is_mock:
            campaigns = self.list_campaigns()
            campaign_ids = [str(camp["id"]) for camp in campaigns]
            rows = self.get_daily_stats(campaign_ids, date_from, date_to)
            return [
                {
                    "date": date.fromisoformat(row["Date"]),
                    "platform": Platform.ozon,
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
                    "conversions": None,
                    "cost": int(float(row.get("Cost") or 0)),
                    "currency": "RUB",
                }
                for row in rows
            ]
        client = self._build_client()

        async def _fetch() -> list[MetricRecord]:
            try:
                campaigns = await client.get_campaigns()
                campaign_ids = [c.get("id") for c in campaigns if c.get("id")]
                if not campaign_ids:
                    return []
                rows = await client.get_statistics(
                    campaign_ids=campaign_ids,
                    date_from=date_from.isoformat(),
                    date_to=date_to.isoformat(),
                    group_by="DATE",
                )
                return [self._map_stat_row(row) for row in rows]
            finally:
                await client.close()

        return [row for row in asyncio.run(_fetch()) if row]

    def stop(self, external_ids: dict) -> None:
        return None

    def list_campaigns(self) -> List[Dict[str, Any]]:
        if self.is_mock:
            return [
                {"id": "ozon_aaa", "name": "Ozon Campaign A", "status": "ACTIVATED"},
                {"id": "ozon_bbb", "name": "Ozon Campaign B", "status": "PAUSED"},
            ]

        client = self._build_client()

        async def _fetch() -> List[Dict[str, Any]]:
            try:
                campaigns = await client.get_campaigns()
                result = []
                for camp in campaigns or []:
                    result.append({
                        "id": camp.get("id") or camp.get("campaignId") or camp.get("campaign_id"),
                        "name": camp.get("title") or camp.get("name") or "Ozon Campaign",
                        "status": camp.get("state") or camp.get("status"),
                    })
                return result
            finally:
                await client.close()

        return asyncio.run(_fetch())

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
                        "Impressions": 500 + (10 if cid == "ozon_aaa" else 20),
                        "Clicks": 50 + (1 if cid == "ozon_aaa" else 2),
                        "Cost": 1000.0
                    })
            return results

        client = self._build_client()

        async def _fetch() -> List[Dict[str, Any]]:
            try:
                rows = await client.get_statistics(
                    campaign_ids=[int(cid) for cid in campaign_ids],
                    date_from=date_from.isoformat(),
                    date_to=date_to.isoformat(),
                    group_by="DATE",
                )
                result = []
                for row in rows or []:
                    mapped = self._map_stat_row(row)
                    if not mapped:
                        continue
                    result.append({
                        "Date": mapped["date"].isoformat(),
                        "CampaignId": mapped["campaign_external_id"],
                        "Impressions": mapped["impressions"],
                        "Clicks": mapped["clicks"],
                        "Cost": mapped["spend"],
                    })
                return result
            finally:
                await client.close()

        return asyncio.run(_fetch())

    def _map_stat_row(self, row: Dict[str, Any]) -> MetricRecord | None:
        if not isinstance(row, dict):
            return None
        campaign_id = row.get("campaignId") or row.get("campaign_id") or row.get("CampaignId")
        date_value = row.get("date") or row.get("Date")
        if not campaign_id or not date_value:
            return None

        def pick(*keys, default=0):
            for key in keys:
                if key in row and row[key] is not None:
                    return row[key]
            return default

        impressions = pick("impressions", "shows", "views", "Impressions")
        clicks = pick("clicks", "Clicks")
        spend = pick("spend", "cost", "Cost")
        revenue = pick("revenue", "sales", "Revenue")

        return {
            "date": date.fromisoformat(str(date_value)),
            "platform": Platform.ozon,
            "level": "campaign",
            "campaign_external_id": str(campaign_id),
            "ad_group_external_id": None,
            "ad_external_id": None,
            "impressions": int(impressions or 0),
            "clicks": int(clicks or 0),
            "spend": int(float(spend or 0)),
            "leads": 0,
            "purchases": int(float(row.get("orders") or 0)),
            "revenue": int(float(revenue or 0)),
            "conversions": None,
            "cost": int(float(spend or 0)),
            "currency": "RUB",
        }
