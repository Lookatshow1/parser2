"""
VK Ads API Client.

API documentation: https://ads.vk.com/help/articles/api
"""
from typing import Dict, List, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class VKAdsClient:
    """
    VK Ads API Client.
    
    Supports 3-level structure: Campaign → Ad Group → Ad
    """
    
    BASE_URL = "https://ads.vk.com/api/v2"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self._client = httpx.AsyncClient(timeout=60.0)
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request to VK Ads."""
        url = f"{self.BASE_URL}/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        if method.upper() == "GET":
            response = await self._client.get(url, headers=headers, params=params)
        else:
            response = await self._client.request(
                method.upper(), url, headers=headers, json=data
            )
        
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # CAMPAIGNS
    # =========================================================================
    
    async def get_campaigns(
        self,
        account_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get list of campaigns."""
        result = await self._request("GET", "campaigns.json", params={
            "account_id": account_id,
            "limit": limit,
            "offset": offset,
        })
        return result.get("items", [])
    
    async def create_campaign(
        self,
        account_id: int,
        name: str,
        objective: str = "traffic",
        budget_limit: Optional[int] = None,
        budget_limit_day: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new campaign.
        
        Args:
            account_id: VK Ads account ID
            name: Campaign name
            objective: traffic, reach, conversions, app_installs, etc.
            budget_limit: Total budget limit (in kopecks)
            budget_limit_day: Daily budget limit (in kopecks)
        """
        data = {
            "account_id": account_id,
            "name": name,
            "objective": objective,
            "status": "active",  # or "blocked"
        }
        
        if budget_limit:
            data["budget_limit"] = budget_limit
        if budget_limit_day:
            data["budget_limit_day"] = budget_limit_day
        
        result = await self._request("POST", "campaigns.json", data=data)
        return result
    
    async def update_campaign_status(
        self,
        campaign_id: int,
        status: str,  # "active" or "blocked"
    ) -> bool:
        """Update campaign status."""
        result = await self._request("POST", f"campaigns/{campaign_id}.json", data={
            "status": status,
        })
        return result.get("id") == campaign_id
    
    # =========================================================================
    # AD GROUPS (Packages in VK terminology)
    # =========================================================================
    
    async def create_ad_group(
        self,
        campaign_id: int,
        name: str,
        targeting: Optional[Dict[str, Any]] = None,
        age_from: int = 18,
        age_to: int = 65,
        sex: str = "all",  # "male", "female", "all"
        geo_type: str = "country",
        countries: List[int] = None,
    ) -> Dict[str, Any]:
        """
        Create ad group with targeting.
        
        Args:
            campaign_id: Parent campaign ID
            name: Ad group name
            targeting: Custom targeting dict
            age_from/age_to: Age targeting
            sex: Gender targeting
            countries: List of country IDs (643 = Russia)
        """
        data = {
            "campaign_id": campaign_id,
            "name": name,
            "status": "active",
            "age_from": age_from,
            "age_to": age_to,
            "sex": sex,
            "geo_type": geo_type,
            "countries": countries or [643],  # Russia
        }
        
        if targeting:
            data.update(targeting)
        
        result = await self._request("POST", "packages.json", data=data)
        return result
    
    async def get_ad_groups(
        self,
        campaign_id: int,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get ad groups for a campaign."""
        result = await self._request("GET", "packages.json", params={
            "campaign_id": campaign_id,
            "limit": limit,
        })
        return result.get("items", [])
    
    # =========================================================================
    # ADS (Banners)
    # =========================================================================
    
    async def create_ad(
        self,
        package_id: int,  # ad group ID
        title: str,
        description: str,
        link_url: str,
        image_url: Optional[str] = None,
        call_to_action: str = "learn_more",
    ) -> Dict[str, Any]:
        """
        Create an ad (banner).
        
        Args:
            package_id: Parent ad group ID
            title: Ad title (up to 33 chars)
            description: Ad text (up to 220 chars for universal posts)
            link_url: Landing page URL
            image_url: Creative image URL
            call_to_action: CTA button type
        """
        data = {
            "package_id": package_id,
            "status": "active",
            "title": title[:33],
            "description": description[:220],
            "link_url": link_url,
            "call_to_action": call_to_action,
        }
        
        if image_url:
            data["image"] = image_url
        
        result = await self._request("POST", "banners.json", data=data)
        return result
    
    async def get_ads(
        self,
        package_id: int,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get ads for an ad group."""
        result = await self._request("GET", "banners.json", params={
            "package_id": package_id,
            "limit": limit,
        })
        return result.get("items", [])
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    async def get_statistics(
        self,
        object_type: str,  # "campaign", "package", "banner"
        object_ids: List[int],
        date_from: str,
        date_to: str,
        metrics: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get statistics for objects.
        
        Args:
            object_type: Type of object
            object_ids: List of object IDs
            date_from/date_to: Date range (YYYY-MM-DD)
            metrics: List of metrics to retrieve
        """
        default_metrics = [
            "shows", "clicks", "ctr", "spent",
            "cpm", "cpc", "reach", "frequency"
        ]
        
        result = await self._request("GET", "statistics.json", params={
            "object_type": object_type,
            "ids": ",".join(str(i) for i in object_ids),
            "date_from": date_from,
            "date_to": date_to,
            "metrics": ",".join(metrics or default_metrics),
        })
        
        return result.get("items", [])
    
    # =========================================================================
    # ACCOUNTS
    # =========================================================================
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get available ad accounts."""
        result = await self._request("GET", "accounts.json")
        return result.get("items", [])
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
