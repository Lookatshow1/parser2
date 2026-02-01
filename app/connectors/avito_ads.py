"""
Avito Ads Connector.

Provides integration with Avito Promotion API for managing ad listings
and their promotion status (VAS - Value Added Services).

API Docs: https://developers.avito.ru/api-catalog/promotion/documentation
"""
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
import httpx

from app.connectors.base import AdsConnector
from app.services.oauth.base import AvitoOAuth, OAuthToken

logger = logging.getLogger(__name__)


# Avito API base URL
AVITO_API_BASE = "https://api.avito.ru"


class AvitoConnector(AdsConnector):
    """
    Connector for Avito Promotion API.
    
    Supports:
    - Fetching listings statistics
    - Applying promotion services (VAS)
    - Getting promotion prices
    """
    
    platform = "avito"
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Avito connector.
        
        Args:
            credentials: Dict containing:
                - client_id: Avito API client ID
                - client_secret: Avito API secret
                - user_id: Avito user/account ID
        """
        self.client_id = credentials.get("client_id", "")
        self.client_secret = credentials.get("client_secret", "")
        self.user_id = credentials.get("user_id", "")
        self._token: Optional[OAuthToken] = None
        self._http_client = httpx.Client(timeout=30.0)
        
        # Restore token from credentials if available
        if "access_token" in credentials:
            from datetime import datetime
            expires_at = credentials.get("expires_at")
            if expires_at:
                self._token = OAuthToken(
                    access_token=credentials["access_token"],
                    token_type=credentials.get("token_type", "Bearer"),
                    expires_at=datetime.fromisoformat(expires_at),
                )
    
    async def _ensure_token(self) -> str:
        """Get valid access token, refreshing if needed."""
        if self._token is None or self._token.is_expired:
            oauth = AvitoOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri="",
            )
            self._token = await oauth.exchange_code("")
            await oauth.close()
        return self._token.access_token
    
    def _get_headers(self, token: str) -> Dict[str, str]:
        """Get API headers with auth token."""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    # =========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS (required by AdsConnector)
    # =========================================================================
    
    def credential_schema(self):
        """Return credential schema for Avito."""
        from pydantic import BaseModel
        
        class AvitoCredentials(BaseModel):
            client_id: str
            client_secret: str
            user_id: str
        
        return AvitoCredentials
    
    def validate_connection(self, credentials_json: dict) -> dict:
        """Validate Avito connection by attempting token fetch."""
        import asyncio
        
        async def _validate():
            try:
                oauth = AvitoOAuth(
                    client_id=credentials_json.get("client_id", ""),
                    client_secret=credentials_json.get("client_secret", ""),
                    redirect_uri="",
                )
                token = await oauth.exchange_code("")
                await oauth.close()
                return {"valid": True, "token": token.access_token[:10] + "..."}
            except Exception as e:
                return {"valid": False, "error": str(e)}
        
        try:
            return asyncio.run(_validate())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_validate())
    
    def create_campaign_bundle(self, plan, experiment, creatives) -> dict:
        """Avito doesn't support campaign creation - items must be created manually."""
        raise NotImplementedError("Avito does not support creating campaigns via API. Create items manually on avito.ru")
    
    def sync_status(self, external_ids: dict) -> dict:
        """Get status of Avito items by their IDs."""
        import asyncio
        
        async def _sync():
            results = {}
            for item_id in external_ids.values():
                try:
                    info = await self.get_item_info(str(item_id))
                    results[item_id] = info.get("status", "unknown")
                except Exception as e:
                    results[item_id] = f"error: {e}"
            return results
        
        try:
            return asyncio.run(_sync())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_sync())
    
    def stop(self, external_ids: dict) -> None:
        """Stop/deactivate Avito items."""
        # Avito API doesn't have direct stop endpoint - items must be managed manually
        logger.warning("Avito items cannot be stopped via API - manage manually on avito.ru")
    
    def list_campaigns(self) -> List[Dict[str, Any]]:
        """List Avito items as 'campaigns'."""
        import asyncio
        
        async def _list():
            items = await self.list_items()
            return [
                {
                    "id": str(item.get("id")),
                    "name": item.get("title", "Untitled"),
                    "status": item.get("status", "unknown"),
                }
                for item in items
            ]
        
        try:
            return asyncio.run(_list())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_list())
    
    def get_daily_stats(self, campaign_ids: List[str], date_from: date, date_to: date) -> List[Dict[str, Any]]:
        """Get daily statistics for Avito items."""
        return self.fetch_metrics(date_from, date_to)
    
    def update_ad_link(self, ad_id: str, link_href: str) -> Dict[str, Any]:
        """Update link for an Avito item."""
        # Avito items are listings with their own URLs, not ad links
        raise NotImplementedError("Avito items have their own URLs and cannot be updated via API")
    
    # =========================================================================
    # LISTINGS & STATISTICS
    # =========================================================================
    
    def fetch_metrics(
        self,
        date_from: date,
        date_to: date,
        connection_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch ad listings with their metrics.
        
        Note: Avito API uses item statistics endpoint.
        """
        # Run async code in sync context
        import asyncio
        
        async def _fetch():
            token = await self._ensure_token()
            
            # Get items (listings)
            items_url = f"{AVITO_API_BASE}/core/v1/items"
            headers = self._get_headers(token)
            
            response = self._http_client.get(
                items_url,
                headers=headers,
                params={"per_page": 100},
            )
            response.raise_for_status()
            data = response.json()
            
            items = data.get("resources", [])
            metrics = []
            
            for item in items:
                item_id = str(item.get("id"))
                
                # Get item statistics
                stats_url = f"{AVITO_API_BASE}/stats/v1/accounts/{self.user_id}/items/{item_id}"
                stats_response = self._http_client.get(
                    stats_url,
                    headers=headers,
                    params={
                        "dateFrom": date_from.isoformat(),
                        "dateTo": date_to.isoformat(),
                    },
                )
                
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    
                    metrics.append({
                        "date": date_to.isoformat(),
                        "level": "ad",
                        "campaign_external_id": "avito_listings",
                        "ad_group_external_id": item.get("category", {}).get("id", "default"),
                        "ad_external_id": item_id,
                        "impressions": stats.get("views", 0),
                        "clicks": stats.get("contacts", 0),  # contacts = phone views + messages
                        "spend": 0,  # Would need promotion data
                        "leads": stats.get("favorites", 0),
                    })
            
            return metrics
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _fetch())
                    return future.result()
            else:
                return loop.run_until_complete(_fetch())
        except RuntimeError:
            return asyncio.run(_fetch())
    
    # =========================================================================
    # PROMOTION SERVICES (VAS)
    # =========================================================================
    
    async def get_promotion_prices(self, item_id: str) -> Dict[str, Any]:
        """
        Get available promotion services and their prices for an item.
        
        VAS types:
        - highlight: Highlighting the ad
        - xl: XL format (larger image)
        - pushUp: Push up in search results
        - turboSale: Turbo sale package
        """
        token = await self._ensure_token()
        
        url = f"{AVITO_API_BASE}/core/v1/accounts/{self.user_id}/items/{item_id}/vas_prices"
        response = self._http_client.get(url, headers=self._get_headers(token))
        response.raise_for_status()
        
        return response.json()
    
    async def apply_promotion(self, item_id: str, vas_type: str) -> Dict[str, Any]:
        """
        Apply a promotion service to an item.
        
        Args:
            item_id: Avito item ID
            vas_type: One of 'highlight', 'xl', 'pushUp', 'turboSale'
        
        Returns:
            API response with applied VAS info
        """
        token = await self._ensure_token()
        
        url = f"{AVITO_API_BASE}/core/v1/accounts/{self.user_id}/items/{item_id}/vas"
        response = self._http_client.post(
            url,
            headers=self._get_headers(token),
            json={"vas_type": vas_type},
        )
        response.raise_for_status()
        
        return response.json()
    
    # =========================================================================
    # ITEM MANAGEMENT
    # =========================================================================
    
    async def list_items(self, status: str = "active") -> List[Dict[str, Any]]:
        """
        List all items (ad listings) for the account.
        
        Args:
            status: Filter by status ('active', 'removed', 'old', 'blocked')
        """
        token = await self._ensure_token()
        
        url = f"{AVITO_API_BASE}/core/v1/items"
        response = self._http_client.get(
            url,
            headers=self._get_headers(token),
            params={"status": status, "per_page": 100},
        )
        response.raise_for_status()
        
        return response.json().get("resources", [])
    
    async def get_item_info(self, item_id: str) -> Dict[str, Any]:
        """Get detailed information about an item."""
        token = await self._ensure_token()
        
        url = f"{AVITO_API_BASE}/core/v1/accounts/{self.user_id}/items/{item_id}"
        response = self._http_client.get(url, headers=self._get_headers(token))
        response.raise_for_status()
        
        return response.json()
    
    # =========================================================================
    # MESSAGES & LEADS
    # =========================================================================
    
    async def get_unread_chats(self) -> List[Dict[str, Any]]:
        """Get list of unread chats (potential leads)."""
        token = await self._ensure_token()
        
        url = f"{AVITO_API_BASE}/messenger/v2/accounts/{self.user_id}/chats"
        response = self._http_client.get(
            url,
            headers=self._get_headers(token),
            params={"unread_only": True},
        )
        response.raise_for_status()
        
        return response.json().get("chats", [])
    
    def close(self):
        """Close HTTP client."""
        self._http_client.close()
    
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
