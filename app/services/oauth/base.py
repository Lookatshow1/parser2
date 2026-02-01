"""
OAuth Base Module for Ad Platforms.

Provides common OAuth2 functionality for Yandex Direct, VK Ads, and Ozon Performance.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)


@dataclass
class OAuthToken:
    """OAuth token with metadata."""
    access_token: str
    token_type: str
    expires_at: datetime
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 5 min buffer)."""
        return datetime.utcnow() >= (self.expires_at - timedelta(minutes=5))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat(),
            "refresh_token": self.refresh_token,
            "scope": self.scope,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OAuthToken":
        """Deserialize from dict."""
        return cls(
            access_token=data["access_token"],
            token_type=data["token_type"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
        )


class OAuthProvider(ABC):
    """Abstract OAuth2 provider for ad platforms."""
    
    platform_name: str = "unknown"
    authorize_url: str = ""
    token_url: str = ""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._http_client = httpx.AsyncClient(timeout=30.0)
    
    def get_authorization_url(self, state: str, scope: Optional[str] = None) -> str:
        """Generate OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
        }
        if scope:
            params["scope"] = scope
        
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorize_url}?{query}"
    
    @abstractmethod
    async def exchange_code(self, code: str) -> OAuthToken:
        """Exchange authorization code for access token."""
        pass
    
    @abstractmethod
    async def refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Refresh expired access token."""
        pass
    
    async def close(self):
        """Close HTTP client."""
        await self._http_client.aclose()


class YandexOAuth(OAuthProvider):
    """
    Yandex OAuth2 Provider.
    
    Docs: https://yandex.ru/dev/id/doc/ru/concepts/ya-oauth-intro
    """
    
    platform_name = "yandex"
    authorize_url = "https://oauth.yandex.ru/authorize"
    token_url = "https://oauth.yandex.ru/token"
    
    async def exchange_code(self, code: str) -> OAuthToken:
        """Exchange code for Yandex token."""
        response = await self._http_client.post(
            self.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        expires_in = data.get("expires_in", 3600)
        return OAuthToken(
            access_token=data["access_token"],
            token_type=data.get("token_type", "bearer"),
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            refresh_token=data.get("refresh_token"),
        )
    
    async def refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Refresh Yandex token."""
        if not token.refresh_token:
            raise ValueError("No refresh token available")
        
        response = await self._http_client.post(
            self.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        expires_in = data.get("expires_in", 3600)
        return OAuthToken(
            access_token=data["access_token"],
            token_type=data.get("token_type", "bearer"),
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            refresh_token=data.get("refresh_token", token.refresh_token),
        )


class VKAdsOAuth(OAuthProvider):
    """
    VK Ads OAuth2 Provider.
    
    Docs: https://ads.vk.com/help/articles/api
    """
    
    platform_name = "vk"
    authorize_url = "https://ads.vk.com/oauth/authorize"
    token_url = "https://ads.vk.com/api/v2/oauth2/token.json"
    
    async def exchange_code(self, code: str) -> OAuthToken:
        """Exchange code for VK Ads token (or use client credentials)."""
        response = await self._http_client.post(
            self.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        # VK tokens are valid for 24 hours
        expires_in = data.get("expires_in", 86400)
        return OAuthToken(
            access_token=data["access_token"],
            token_type=data.get("token_type", "bearer"),
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            refresh_token=data.get("refresh_token"),
        )
    
    async def get_client_credentials_token(self) -> OAuthToken:
        """Get token using client credentials (for agency accounts)."""
        response = await self._http_client.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        expires_in = data.get("expires_in", 86400)
        return OAuthToken(
            access_token=data["access_token"],
            token_type=data.get("token_type", "bearer"),
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
        )
    
    async def refresh_token(self, token: OAuthToken) -> OAuthToken:
        """VK uses client credentials refresh."""
        return await self.get_client_credentials_token()


class OzonOAuth(OAuthProvider):
    """
    Ozon Performance OAuth2 Provider.
    
    Docs: https://docs.ozon.ru/api/performance/
    Host changed to api-performance.ozon.ru as of Jan 2025
    """
    
    platform_name = "ozon"
    authorize_url = "https://seller.ozon.ru/app/settings/api-keys"  # Manual key generation
    token_url = "https://api-performance.ozon.ru/api/client/token"
    
    async def exchange_code(self, code: str) -> OAuthToken:
        """
        Ozon uses client credentials with manual key generation.
        The 'code' here is actually the client_secret from Ozon.
        """
        response = await self._http_client.post(
            self.token_url,
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        data = response.json()
        
        # Ozon tokens are valid for 30 minutes
        expires_in = data.get("expires_in", 1800)
        return OAuthToken(
            access_token=data["access_token"],
            token_type="Bearer",
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
        )
    
    async def refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Refresh Ozon token (get new one via client credentials)."""
        return await self.exchange_code("")


class AvitoOAuth(OAuthProvider):
    """
    Avito OAuth2 Provider.
    
    Docs: https://developers.avito.ru/api-catalog
    Uses OAuth2 Client Credentials flow for API access.
    Requires paid business tariff (Basic/Extended/Maximum).
    """
    
    platform_name = "avito"
    authorize_url = "https://www.avito.ru/oauth"
    token_url = "https://api.avito.ru/token/"
    
    async def exchange_code(self, code: str) -> OAuthToken:
        """
        Avito uses client credentials grant.
        The 'code' parameter is not used - we use client_id/client_secret.
        """
        response = await self._http_client.post(
            self.token_url,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        data = response.json()
        
        # Avito tokens are valid for 24 hours
        expires_in = data.get("expires_in", 86400)
        return OAuthToken(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
        )
    
    async def refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Refresh Avito token (get new one via client credentials)."""
        return await self.exchange_code("")


# Provider registry
OAUTH_PROVIDERS = {
    "yandex": YandexOAuth,
    "vk": VKAdsOAuth,
    "ozon": OzonOAuth,
    "avito": AvitoOAuth,
}


def get_oauth_provider(
    platform: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> OAuthProvider:
    """Get OAuth provider for platform."""
    provider_class = OAUTH_PROVIDERS.get(platform)
    if not provider_class:
        raise ValueError(f"Unknown platform: {platform}")
    return provider_class(client_id, client_secret, redirect_uri)
