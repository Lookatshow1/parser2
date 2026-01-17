"""
Ozon Performance API Client.

API documentation: https://docs.ozon.ru/api/performance/
Host: api-performance.ozon.ru (as of Jan 2025)
"""
from typing import Dict, List, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class OzonPerformanceClient:
    """
    Ozon Performance API Client.
    
    Supports CPC campaigns, product promotion, and statistics.
    """
    
    BASE_URL = "https://api-performance.ozon.ru/api/client"
    
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
        """Make API request to Ozon Performance."""
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
        
        # Ozon returns empty response for some endpoints
        if response.text:
            return response.json()
        return {"success": True}
    
    # =========================================================================
    # CAMPAIGNS
    # =========================================================================
    
    async def get_campaigns(
        self,
        state: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get list of campaigns.
        
        Args:
            state: Filter by state (CAMPAIGN_STATE_RUNNING, etc.)
        """
        params = {"limit": limit, "offset": offset}
        if state:
            params["state"] = state
        
        result = await self._request("GET", "campaign", params=params)
        return result.get("list", [])
    
    async def create_cpc_campaign(
        self,
        title: str,
        product_ids: List[int],
        daily_budget: int = 500,  # In rubles
        placement: str = "PLACEMENT_PDP",  # Product detail page
    ) -> Dict[str, Any]:
        """
        Create a CPC (cost-per-click) campaign.
        
        Args:
            title: Campaign name
            product_ids: List of product SKUs to promote
            daily_budget: Daily budget in rubles
            placement: Ad placement type
                - PLACEMENT_PDP: Product detail page
                - PLACEMENT_SEARCH_AND_CATEGORY: Search results
        """
        data = {
            "title": title,
            "daily_budget": str(daily_budget),  # API expects string
            "placement": placement,
            "product_autopilot_strategy": "NO_CONTROL",  # or "MIN_PRICE"
            "products": [{"sku": str(pid)} for pid in product_ids],
        }
        
        result = await self._request("POST", "campaign/cpc/v2/product", data=data)
        return result
    
    async def activate_campaign(self, campaign_id: int) -> bool:
        """Activate a campaign."""
        result = await self._request(
            "POST", 
            f"campaign/{campaign_id}/v2/activate",
            data={}
        )
        return result.get("success", False)
    
    async def deactivate_campaign(self, campaign_id: int) -> bool:
        """Deactivate a campaign."""
        result = await self._request(
            "POST",
            f"campaign/{campaign_id}/v2/deactivate", 
            data={}
        )
        return result.get("success", False)
    
    async def get_campaign_details(self, campaign_id: int) -> Dict[str, Any]:
        """Get campaign details."""
        result = await self._request("GET", f"campaign/{campaign_id}")
        return result
    
    # =========================================================================
    # PRODUCTS
    # =========================================================================
    
    async def add_products_to_campaign(
        self,
        campaign_id: int,
        product_ids: List[int],
    ) -> Dict[str, Any]:
        """Add products to an existing campaign."""
        data = {
            "products": [{"sku": str(pid)} for pid in product_ids],
        }
        
        result = await self._request(
            "POST",
            f"campaign/{campaign_id}/products",
            data=data
        )
        return result
    
    async def get_campaign_products(
        self,
        campaign_id: int,
    ) -> List[Dict[str, Any]]:
        """Get products in a campaign."""
        result = await self._request(
            "GET",
            f"campaign/{campaign_id}/products"
        )
        return result.get("products", [])
    
    async def set_product_bids(
        self,
        campaign_id: int,
        bids: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Set bids for products in a campaign.
        
        Args:
            bids: List of {"sku": "123", "bid": "50"} dicts
                  bid is in rubles
        """
        result = await self._request(
            "POST",
            f"campaign/{campaign_id}/products/bids",
            data={"bids": bids}
        )
        return result
    
    async def get_competitive_bids(
        self,
        campaign_id: int,
    ) -> List[Dict[str, Any]]:
        """Get competitive bid information for products."""
        result = await self._request(
            "GET",
            f"campaign/{campaign_id}/products/bids/competitive"
        )
        return result.get("products", [])
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    async def get_statistics(
        self,
        campaign_ids: List[int],
        date_from: str,
        date_to: str,
        group_by: str = "DATE",  # DATE, NO (totals only)
    ) -> List[Dict[str, Any]]:
        """
        Get campaign statistics.
        
        Args:
            campaign_ids: List of campaign IDs
            date_from/date_to: Date range (YYYY-MM-DD)
            group_by: Grouping option
        """
        data = {
            "campaigns": [str(c) for c in campaign_ids],
            "dateFrom": date_from,
            "dateTo": date_to,
            "groupBy": group_by,
        }
        
        result = await self._request("POST", "statistics", data=data)
        return result.get("rows", [])
    
    async def get_daily_statistics(
        self,
        campaign_id: int,
        date_from: str,
        date_to: str,
    ) -> List[Dict[str, Any]]:
        """Get daily statistics for a campaign."""
        result = await self._request(
            "GET",
            f"campaign/{campaign_id}/statistics/daily",
            params={"dateFrom": date_from, "dateTo": date_to}
        )
        return result.get("days", [])
    
    # =========================================================================
    # BALANCE
    # =========================================================================
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance information."""
        result = await self._request("GET", "finance/balance")
        return result
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
