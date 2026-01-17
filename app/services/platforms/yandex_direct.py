"""
Yandex Direct API Client.

API v5 documentation: https://yandex.ru/dev/direct/doc/dg/concepts/about.html
"""
from typing import Dict, List, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class YandexDirectClient:
    """
    Yandex Direct API v5 Client.
    
    Supports campaign, ad group, and ad management.
    """
    
    BASE_URL = "https://api.direct.yandex.com/json/v5"
    SANDBOX_URL = "https://api-sandbox.direct.yandex.com/json/v5"
    
    def __init__(self, access_token: str, use_sandbox: bool = False):
        self.access_token = access_token
        self.base_url = self.SANDBOX_URL if use_sandbox else self.BASE_URL
        self._client = httpx.AsyncClient(timeout=60.0)
    
    async def _request(self, service: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to Yandex Direct."""
        url = f"{self.base_url}/{service}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept-Language": "ru",
        }
        
        payload = {
            "method": method,
            "params": params,
        }
        
        response = await self._client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if "error" in data:
            raise Exception(f"Yandex Direct API Error: {data['error']}")
        
        return data.get("result", {})
    
    # =========================================================================
    # CAMPAIGNS
    # =========================================================================
    
    async def get_campaigns(
        self,
        states: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get list of campaigns."""
        selection_criteria = {}
        if states:
            selection_criteria["States"] = states
        
        result = await self._request("campaigns", "get", {
            "SelectionCriteria": selection_criteria,
            "FieldNames": [
                "Id", "Name", "Status", "State", "Type",
                "StartDate", "EndDate", "DailyBudget", "Statistics"
            ],
            "Page": {"Limit": limit},
        })
        
        return result.get("Campaigns", [])
    
    async def create_campaign(
        self,
        name: str,
        campaign_type: str = "TEXT_CAMPAIGN",
        daily_budget: int = 1000000,  # In micro-units (1 RUB = 1000000)
        start_date: Optional[str] = None,
        negative_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new campaign.
        
        Args:
            name: Campaign name
            campaign_type: TEXT_CAMPAIGN, DYNAMIC_TEXT_CAMPAIGN, etc.
            daily_budget: Daily budget in micro-units
            start_date: Start date in YYYY-MM-DD format
        """
        from datetime import datetime
        
        campaign = {
            "Name": name,
            "StartDate": start_date or datetime.now().strftime("%Y-%m-%d"),
            "DailyBudget": {
                "Amount": daily_budget,
                "Mode": "STANDARD",
            },
        }
        
        # Campaign type specific settings
        if campaign_type == "TEXT_CAMPAIGN":
            campaign["TextCampaign"] = {
                "BiddingStrategy": {
                    "Search": {
                        "BiddingStrategyType": "HIGHEST_POSITION",
                    },
                    "Network": {
                        "BiddingStrategyType": "SERVING_OFF",
                    },
                },
                "Settings": [
                    {"Option": "ADD_METRICA_TAG", "Value": "YES"},
                    {"Option": "ADD_TO_FAVORITES", "Value": "NO"},
                ],
            }
            if negative_keywords:
                campaign["TextCampaign"]["NegativeKeywords"] = {
                    "Items": negative_keywords
                }
        
        result = await self._request("campaigns", "add", {
            "Campaigns": [campaign],
        })
        
        return result.get("AddResults", [{}])[0]
    
    async def update_campaign_status(
        self,
        campaign_id: int,
        action: str,  # "suspend", "resume", "archive", "unarchive"
    ) -> bool:
        """Update campaign status."""
        method_map = {
            "suspend": "suspend",
            "resume": "resume", 
            "archive": "archive",
            "unarchive": "unarchive",
        }
        
        method = method_map.get(action)
        if not method:
            raise ValueError(f"Unknown action: {action}")
        
        result = await self._request("campaigns", method, {
            "SelectionCriteria": {"Ids": [campaign_id]},
        })
        
        return bool(result.get("SuspendResults") or result.get("ResumeResults"))
    
    # =========================================================================
    # AD GROUPS
    # =========================================================================
    
    async def create_ad_group(
        self,
        campaign_id: int,
        name: str,
        region_ids: List[int] = None,
        negative_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create ad group within a campaign."""
        ad_group = {
            "Name": name,
            "CampaignId": campaign_id,
            "RegionIds": region_ids or [225],  # 225 = Russia
        }
        
        if negative_keywords:
            ad_group["NegativeKeywords"] = {"Items": negative_keywords}
        
        result = await self._request("adgroups", "add", {
            "AdGroups": [ad_group],
        })
        
        return result.get("AddResults", [{}])[0]
    
    async def get_ad_groups(
        self,
        campaign_ids: List[int],
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get ad groups for campaigns."""
        result = await self._request("adgroups", "get", {
            "SelectionCriteria": {"CampaignIds": campaign_ids},
            "FieldNames": ["Id", "Name", "CampaignId", "Status", "RegionIds"],
            "Page": {"Limit": limit},
        })
        
        return result.get("AdGroups", [])
    
    # =========================================================================
    # ADS
    # =========================================================================
    
    async def create_text_ad(
        self,
        ad_group_id: int,
        title: str,
        title2: Optional[str] = None,
        text: str = "",
        href: str = "",
        display_url_path: Optional[str] = None,
        sitelinks: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a text ad.
        
        Args:
            title: Main headline (up to 35 chars)
            title2: Second headline (up to 30 chars)
            text: Ad text (up to 81 chars)
            href: Landing page URL
            sitelinks: List of {"Title": "...", "Href": "..."} dicts
        """
        ad = {
            "AdGroupId": ad_group_id,
            "TextAd": {
                "Title": title[:35],
                "Text": text[:81],
                "Href": href,
                "Mobile": "NO",
            },
        }
        
        if title2:
            ad["TextAd"]["Title2"] = title2[:30]
        
        if display_url_path:
            ad["TextAd"]["DisplayUrlPath"] = display_url_path
        
        if sitelinks:
            ad["TextAd"]["SitelinkSetId"] = await self._create_sitelink_set(sitelinks)
        
        result = await self._request("ads", "add", {
            "Ads": [ad],
        })
        
        return result.get("AddResults", [{}])[0]
    
    async def _create_sitelink_set(self, sitelinks: List[Dict[str, str]]) -> int:
        """Create a sitelink set and return its ID."""
        sitelink_items = [
            {"Title": s["Title"][:30], "Href": s["Href"]}
            for s in sitelinks[:4]  # Max 4 sitelinks
        ]
        
        result = await self._request("sitelinks", "add", {
            "SitelinksSets": [{"Sitelinks": sitelink_items}],
        })
        
        return result.get("AddResults", [{}])[0].get("Id")
    
    async def get_ads(
        self,
        ad_group_ids: List[int],
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get ads for ad groups."""
        result = await self._request("ads", "get", {
            "SelectionCriteria": {"AdGroupIds": ad_group_ids},
            "FieldNames": ["Id", "AdGroupId", "Status", "State", "Type"],
            "TextAdFieldNames": ["Title", "Title2", "Text", "Href", "DisplayUrlPath"],
            "Page": {"Limit": limit},
        })
        
        return result.get("Ads", [])
    
    # =========================================================================
    # KEYWORDS
    # =========================================================================
    
    async def add_keywords(
        self,
        ad_group_id: int,
        keywords: List[str],
        bid: int = 300000,  # 0.3 RUB in micro-units
    ) -> List[Dict[str, Any]]:
        """Add keywords to ad group."""
        keyword_items = [
            {
                "AdGroupId": ad_group_id,
                "Keyword": kw,
                "Bid": bid,
            }
            for kw in keywords
        ]
        
        result = await self._request("keywords", "add", {
            "Keywords": keyword_items,
        })
        
        return result.get("AddResults", [])
    
    # =========================================================================
    # REPORTS
    # =========================================================================
    
    async def get_campaign_stats(
        self,
        campaign_ids: List[int],
        date_from: str,
        date_to: str,
    ) -> List[Dict[str, Any]]:
        """Get campaign statistics."""
        result = await self._request("reports", "get", {
            "SelectionCriteria": {
                "DateFrom": date_from,
                "DateTo": date_to,
                "Filter": [
                    {"Field": "CampaignId", "Operator": "IN", "Values": [str(c) for c in campaign_ids]}
                ],
            },
            "FieldNames": [
                "CampaignId", "Impressions", "Clicks", "Ctr",
                "Cost", "AvgCpc", "Conversions", "CostPerConversion"
            ],
            "ReportName": "Campaign Stats",
            "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "YES",
        })
        
        return result
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
