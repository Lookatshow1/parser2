from __future__ import annotations

import os
import datetime
from datetime import date, timedelta
from typing import List, Dict, Any

from pydantic import ValidationError

from app.connectors.base import AdsConnector, MetricRecord
from app.connectors.credentials import VkCredentials
from app.services.platforms.vk_ads import VKAdsClient  # Use new client
from app.core.config import get_settings
from app.db.models import MetricSnapshot, Platform


class VKAdsConnector(AdsConnector):
    def __init__(self, credentials_json: dict | None = None) -> None:
        self._credentials = credentials_json or {}
        self.is_mock = os.getenv("VK_ADS_MOCK", "0") == "1"
        self._settings = get_settings()

    def credential_schema(self):
        return VkCredentials

    def validate_connection(self, credentials_json: dict) -> dict:
        try:
            # We allow partial credentials if we have global settings
            if not credentials_json.get("access_token") and self._settings.vk_ads_client_id:
                 pass # We will try to get token later
            else:
                 self.credential_schema().model_validate(credentials_json)
        except ValidationError as exc:
            return {
                "ok": False,
                "error_code": "invalid_credentials",
                "message": exc.errors()[0]["msg"],
            }
        return {"ok": True}

    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        if self.is_mock:
            return {"campaign_id": "vk_stub_999"}

        import asyncio
        return asyncio.run(self._create_campaign_bundle_async(plan, experiment, creatives))

    async def _create_campaign_bundle_async(self, plan, experiment, creatives) -> dict:
        client = self._build_client()
        try:
            # 1. Create Campaign
            campaign_data = {
                "name": f"Exp {experiment.id} - VK",
                "objective": "site_conversions", # default for now
                "package_id": None, # For apps
            }
            # Look for site url in creatives
            target_url = "https://example.com"
            for c in creatives:
                 if c.platform.value == "vk" and c.target_url:
                      target_url = c.target_url
                      break
            
            # VK Ads V2 Campaign structure might differ, simplified for MVP
            # POST /api/v2/campaigns.json
            cmp_res = await client._request("POST", "campaigns.json", json=campaign_data)
            campaign_id = cmp_res.get("id")
            if not campaign_id:
                 raise ValueError(f"VK Campaign Create Failed: {cmp_res}")

            # 2. Create Ad Group
            ad_group_data = {
                "campaign_id": campaign_id,
                "name": "Ad Group 1",
                # "budget": 100.0,
            }
            grp_res = await client._request("POST", "ad_groups.json", json=ad_group_data)
            ad_group_id = grp_res.get("id")

            # 3. Create Ads
            for creative in creatives:
                if creative.platform.value != "vk":
                    continue
                
                ad_data = {
                    "ad_group_id": ad_group_id,
                    "title": creative.title,
                    "text": creative.text,
                    # "banner": { ... } # Needs image upload usually
                    "url": creative.target_url or target_url
                }
                # For MVP we might skip image upload or use a stock id
                await client._request("POST", "ads.json", json=ad_data)
            
            return {"campaign_id": str(campaign_id)}
        finally:
             await client.close()

    def stop_campaign(self, campaign_external_id: str) -> bool:
        """
        Stops (suspends) a campaign.
        Returns True if successful, False otherwise.
        """
        if self.is_mock:
            return True

        # Need async execution for VKAdsClient
        import asyncio
        return asyncio.run(self._stop_campaign_async(campaign_external_id))

    async def _stop_campaign_async(self, campaign_id: str) -> bool:
        client = self._build_client()
        try:
             # campaign_id can be int or str, api likely expects int
             cid = int(campaign_id)
             # V2 API update campaign status: POST /api/v2/campaigns/{id}.json
             # Body: { "status": "stopped" } (or "paused"?)
             # Usually "stopped" means archived, "paused" means paused. 
             # Let's check typical VK Ads statuses. "active", "paused", "stopped".
             
             data = {"status": "paused"} 
             # Check if update_campaign method exists or use generic request
             # Using generic request for now as client might not have specific update method
             endpoint = f"campaigns/{cid}.json"
             
             # We assume _request handles data as json body for POST/PUT if not GET
             # VKAdsClient._request signature: method, endpoint, params=None, data=None, json=None
             # Use json parameter
             
             await client._request("POST", endpoint, json=data)
             return True
        except Exception as exc:
            print(f"VK stop_campaign failed: {exc}")
            return False
        finally:
            await client.close()

    def sync_status(self, external_ids: dict) -> dict:
        # TODO: Implement status check using new client
        return {"campaign_id": "active"}

    def list_campaigns(self) -> List[Dict[str, Any]]:
        """List all campaigns from VK Ads."""
        if self.is_mock:
             return [
                {"id": 111, "name": "VK Mock 1", "status": "active"},
                {"id": 222, "name": "VK Mock 2", "status": "paused"},
            ]
        import asyncio
        return asyncio.run(self._list_campaigns_async())

    async def _list_campaigns_async(self):
        client = self._build_client()
        try:
            account_id = await self._resolve_account_id(client)
            results = await client.get_campaigns(account_id=account_id, limit=50)
            return [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "status": item.get("status"),
                }
                for item in results or []
            ]
        finally:
            await client.close()

    def fetch_metrics(self, date_from: date, date_to: date, connection_id: int | None = None) -> list[MetricRecord]:
        # This method is used by sync_connection_metrics (generic sync)
        if self.is_mock:
            return self._mock_metrics(date_from, date_to)

        # We need async execution here as VKAdsClient is async
        import asyncio
        return asyncio.run(self._fetch_metrics_async(date_from, date_to))

    async def _fetch_metrics_async(self, date_from: date, date_to: date) -> list[MetricRecord]:
        client = self._build_client()
        try:
            # 1. Get stats for all campaigns
            # We need to know which campaigns to fetch? Or fetch all for account?
            # VK Ads allows fetching by object_type="campaign" and empty IDs? No, IDs required usually.
            
            # Step 1: Get campaigns
            account_id = await self._resolve_account_id(client)
            campaigns = await client.get_campaigns(account_id=account_id, limit=100)
            if not campaigns:
                return []
                
            campaign_ids = [c["id"] for c in campaigns if c.get("id")]
            
            # Step 2: Get stats
            metrics = await client.get_statistics(
                object_type="campaign",
                object_ids=campaign_ids,
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
                metrics=["shows", "clicks", "spent", "ctr", "cpc", "cpm"]
            )
            
            records = []
            for row in metrics:
                # row example: {'id': 123, 'rows': [{'date': '2023-01-01', 'shows': 100, ...}]}
                # Wait, structure depends on API version. 
                # VK Ads API v2 stats structure:
                # items: [{id: ..., rows: [...]}]
                
                campaign_id = row["id"]
                for day_stat in row.get("rows", []):
                    records.append({
                        "date": date.fromisoformat(day_stat["date"]),
                        "platform": Platform.vk,
                        "level": "campaign",
                        "campaign_external_id": str(campaign_id),
                        "ad_group_external_id": None,
                        "ad_external_id": None,
                        "impressions": int(day_stat.get("shows") or 0),
                        "clicks": int(day_stat.get("clicks") or 0),
                        "spend": float(day_stat.get("spent") or 0), # kopecks or rubles? usually string float in json
                        "leads": 0,
                        "purchases": 0,
                        "revenue": 0,
                        "currency": "RUB",
                        "metrics": day_stat # Store raw
                    })
            return records
        finally:
            await client.close()

    def get_daily_stats(self, campaign_ids, date_from: date, date_to: date):
        # Used by sync_metrics (legacy campaign sync)
        import asyncio
        return asyncio.run(self._get_daily_stats_async(campaign_ids, date_from, date_to))

    async def _get_daily_stats_async(self, campaign_ids, date_from, date_to):
        client = self._build_client()
        try:
            metrics = await client.get_statistics(
                object_type="campaign",
                object_ids=[int(i) for i in campaign_ids],
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
                metrics=["shows", "clicks", "spent"]
            )
            
            results = []
            for row in metrics:
                campaign_id = row["id"]
                for day_stat in row.get("rows", []):
                     results.append({
                        "Date": day_stat["date"],
                        "CampaignId": campaign_id,
                        "Impressions": day_stat.get("shows", 0),
                        "Clicks": day_stat.get("clicks", 0),
                        "Cost": day_stat.get("spent", 0),
                     })
            return results
        finally:
            await client.close()

    def _build_client(self) -> VKAdsClient:
        token = self._credentials.get("access_token") or self._credentials.get("token")
        
        # If no token, try Client Credentials flow if configured
        if not token:
            token = os.getenv("VK_ADS_ACCESS_TOKEN")

        if not token:
            raise ValueError("VK Access Token is missing")
            
        return VKAdsClient(access_token=token)

    async def _resolve_account_id(self, client: VKAdsClient) -> int:
        account_id = self._credentials.get("account_id")
        if account_id:
            return int(account_id)
        accounts = await client.get_accounts()
        if not accounts:
            raise ValueError("VK Ads account not found")
        account_id = accounts[0].get("id")
        if not account_id:
            raise ValueError("VK Ads account id missing")
        self._credentials["account_id"] = account_id
        return int(account_id)

    def _mock_metrics(self, date_from, date_to):
        delta = date_to - date_from
        records = []
        for i in range(delta.days + 1):
             d = date_from + timedelta(days=i)
             records.append({
                 "date": d,
                 "platform": Platform.vk,
                 "level": "campaign",
                 "campaign_external_id": "vk_mock_1",
                 "impressions": 1000,
                 "clicks": 50,
                 "spend": 500.0,
                 "currency": "RUB",
                 "metrics": {}
             })
        return records
