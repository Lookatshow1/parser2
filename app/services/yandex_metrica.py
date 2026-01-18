"""
Yandex Metrica Integration Service.

Provides OAuth authentication and API access to Yandex Metrica
for conversion tracking and cross-analytics.

API Docs: https://yandex.ru/dev/metrika/doc/api2/concept/about
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

YANDEX_METRICA_CLIENT_ID = os.getenv("YANDEX_METRICA_CLIENT_ID", "")
YANDEX_METRICA_CLIENT_SECRET = os.getenv("YANDEX_METRICA_CLIENT_SECRET", "")
YANDEX_METRICA_REDIRECT_URI = os.getenv(
    "YANDEX_METRICA_REDIRECT_URI", 
    "https://oauth.yandex.com/verification_code"
)

# OAuth URLs
OAUTH_AUTHORIZE_URL = "https://oauth.yandex.ru/authorize"
OAUTH_TOKEN_URL = "https://oauth.yandex.ru/token"

# Metrica API base
METRICA_API_BASE = "https://api-metrica.yandex.net"

# Required scopes for Metrica
METRICA_SCOPES = "metrika:read"  # metrika:write for creating goals


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MetricaCounter:
    """Yandex Metrica counter (site)."""
    id: int
    name: str
    site: str
    status: str
    create_time: datetime
    
    
@dataclass
class MetricaGoal:
    """Yandex Metrica goal (conversion)."""
    id: int
    name: str
    type: str
    is_retargeting: bool = False
    

@dataclass
class MetricaVisitStats:
    """Aggregated visit statistics."""
    date: str
    visits: int
    page_views: int
    users: int
    bounce_rate: float
    avg_visit_duration: float


# =============================================================================
# YANDEX METRICA SERVICE
# =============================================================================

class YandexMetricaService:
    """
    Service for interacting with Yandex Metrica API.
    
    Provides:
    - OAuth authentication
    - Counters (sites) management
    - Goals and conversions
    - Statistics and reports
    """
    
    def __init__(
        self, 
        access_token: Optional[str] = None,
        client_id: str = YANDEX_METRICA_CLIENT_ID,
        client_secret: str = YANDEX_METRICA_CLIENT_SECRET,
    ):
        self.access_token = access_token
        self.client_id = client_id
        self.client_secret = client_secret
        self._client = httpx.AsyncClient(timeout=30.0)
    
    # -------------------------------------------------------------------------
    # OAuth Methods
    # -------------------------------------------------------------------------
    
    def get_authorization_url(self, state: str = "") -> str:
        """
        Generate OAuth authorization URL for Metrica.
        
        User should be redirected here to grant access.
        Returns URL with metrika:read scope.
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": YANDEX_METRICA_REDIRECT_URI,
            "scope": METRICA_SCOPES,
        }
        if state:
            params["state"] = state
            
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{OAUTH_AUTHORIZE_URL}?{query}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Returns:
            {
                "access_token": str,
                "token_type": str,
                "expires_in": int,
                "refresh_token": str (optional)
            }
        """
        response = await self._client.post(
            OAUTH_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token."""
        response = await self._client.post(
            OAUTH_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        return response.json()
    
    # -------------------------------------------------------------------------
    # Counters (Sites)
    # -------------------------------------------------------------------------
    
    async def get_counters(self) -> List[MetricaCounter]:
        """
        Get list of all Metrica counters (sites) for the user.
        
        API: GET /management/v1/counters
        """
        response = await self._api_request("GET", "/management/v1/counters")
        counters = []
        
        for item in response.get("counters", []):
            counters.append(MetricaCounter(
                id=item["id"],
                name=item.get("name", ""),
                site=item.get("site", ""),
                status=item.get("status", ""),
                create_time=datetime.fromisoformat(
                    item.get("create_time", "2020-01-01T00:00:00").replace("Z", "+00:00")
                ),
            ))
        
        return counters
    
    async def get_counter(self, counter_id: int) -> Optional[MetricaCounter]:
        """Get single counter by ID."""
        response = await self._api_request("GET", f"/management/v1/counter/{counter_id}")
        item = response.get("counter")
        if not item:
            return None
            
        return MetricaCounter(
            id=item["id"],
            name=item.get("name", ""),
            site=item.get("site", ""),
            status=item.get("status", ""),
            create_time=datetime.fromisoformat(
                item.get("create_time", "2020-01-01T00:00:00").replace("Z", "+00:00")
            ),
        )
    
    # -------------------------------------------------------------------------
    # Goals (Conversions)
    # -------------------------------------------------------------------------
    
    async def get_goals(self, counter_id: int) -> List[MetricaGoal]:
        """
        Get all goals for a counter.
        
        API: GET /management/v1/counter/{counterId}/goals
        """
        response = await self._api_request(
            "GET", 
            f"/management/v1/counter/{counter_id}/goals"
        )
        goals = []
        
        for item in response.get("goals", []):
            goals.append(MetricaGoal(
                id=item["id"],
                name=item.get("name", ""),
                type=item.get("type", ""),
                is_retargeting=item.get("is_retargeting", False),
            ))
        
        return goals
    
    # -------------------------------------------------------------------------
    # Statistics & Reports
    # -------------------------------------------------------------------------
    
    async def get_visits_stats(
        self, 
        counter_id: int, 
        date_from: str, 
        date_to: str,
        group: str = "day",
    ) -> List[MetricaVisitStats]:
        """
        Get visit statistics for a counter.
        
        Args:
            counter_id: Metrica counter ID
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            group: Grouping (day, week, month)
        
        API: GET /stat/v1/data
        """
        response = await self._api_request(
            "GET",
            "/stat/v1/data",
            params={
                "id": counter_id,
                "date1": date_from,
                "date2": date_to,
                "metrics": "ym:s:visits,ym:s:pageviews,ym:s:users,ym:s:bounceRate,ym:s:avgVisitDurationSeconds",
                "dimensions": f"ym:s:date{group.capitalize()}",
                "group": group,
            }
        )
        
        stats = []
        for row in response.get("data", []):
            dims = row.get("dimensions", [{}])
            metrics = row.get("metrics", [0, 0, 0, 0, 0])
            
            stats.append(MetricaVisitStats(
                date=dims[0].get("name", "") if dims else "",
                visits=int(metrics[0]) if len(metrics) > 0 else 0,
                page_views=int(metrics[1]) if len(metrics) > 1 else 0,
                users=int(metrics[2]) if len(metrics) > 2 else 0,
                bounce_rate=float(metrics[3]) if len(metrics) > 3 else 0.0,
                avg_visit_duration=float(metrics[4]) if len(metrics) > 4 else 0.0,
            ))
        
        return stats
    
    async def get_conversions(
        self,
        counter_id: int,
        goal_id: int,
        date_from: str,
        date_to: str,
        source_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get conversion data for a specific goal.
        
        Can filter by traffic source (utm_source, etc.)
        """
        params = {
            "id": counter_id,
            "date1": date_from,
            "date2": date_to,
            "metrics": f"ym:s:goal{goal_id}reaches,ym:s:goal{goal_id}conversionRate",
            "dimensions": "ym:s:dateDay",
        }
        
        if source_filter:
            params["filters"] = source_filter
            
        response = await self._api_request("GET", "/stat/v1/data", params=params)
        return response
    
    async def get_attribution_report(
        self,
        counter_id: int,
        date_from: str,
        date_to: str,
    ) -> Dict[str, Any]:
        """
        Get traffic source attribution report.
        
        Shows conversions by source/medium/campaign.
        """
        response = await self._api_request(
            "GET",
            "/stat/v1/data",
            params={
                "id": counter_id,
                "date1": date_from,
                "date2": date_to,
                "metrics": "ym:s:visits,ym:s:users,ym:s:goalReachesAny",
                "dimensions": "ym:s:UTMSource,ym:s:UTMMedium,ym:s:UTMCampaign",
            }
        )
        return response
    
    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------
    
    async def _api_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API request to Metrica."""
        if not self.access_token:
            raise ValueError("Access token not set. Please authenticate first.")
        
        url = f"{METRICA_API_BASE}{endpoint}"
        headers = {
            "Authorization": f"OAuth {self.access_token}",
            "Content-Type": "application/json",
        }
        
        try:
            response = await self._client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Metrica API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.exception("Metrica API request failed")
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()


# =============================================================================
# FACTORY
# =============================================================================

def get_metrica_service(access_token: Optional[str] = None) -> YandexMetricaService:
    """Get Yandex Metrica service instance."""
    return YandexMetricaService(access_token=access_token)
