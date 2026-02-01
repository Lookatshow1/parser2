"""
OAuth API endpoints for ad platform connections.

Provides OAuth authorization URL generation and code exchange for:
- Yandex Direct
- VK Ads  
- Ozon Performance
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import secrets
import logging

from app.db.session import get_db
from app.db.models import Connection, Platform
from app.core.config import get_settings
from app.api.deps import get_current_user, get_current_org
from app.db.models import User, Organization
from app.services.oauth.base import get_oauth_provider, OAuthToken
from app.security.credentials_crypto import maybe_encrypt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/oauth", tags=["oauth"])

# In-memory state store (use Redis in production)
_oauth_states: dict[str, dict] = {}


class OAuthURLResponse(BaseModel):
    url: str
    state: str


class OAuthExchangeRequest(BaseModel):
    platform: str
    code: str
    state: Optional[str] = None
    account_id: Optional[str] = None  # For VK


class OAuthExchangeResponse(BaseModel):
    connection_id: int
    platform: str
    message: str


def _get_platform_config(platform: str):
    """Get OAuth config for platform."""
    settings = get_settings()
    
    if platform == "yandex":
        return {
            "client_id": settings.yandex_client_id,
            "client_secret": settings.yandex_client_secret,
            "redirect_uri": settings.yandex_redirect_uri,
            "scope": "direct:read",
        }
    elif platform == "vk":
        return {
            "client_id": settings.vk_ads_client_id,
            "client_secret": settings.vk_ads_client_secret,
            "redirect_uri": settings.vk_ads_redirect_uri,
            "scope": "ads_manager,read_ads",
        }
    elif platform == "ozon":
        # Ozon uses API keys, not OAuth
        return None
    else:
        return None


@router.get("/{platform}/url", response_model=OAuthURLResponse)
async def get_oauth_url(
    platform: str,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """
    Get OAuth authorization URL for a platform.
    
    The user should be redirected to this URL to authorize their ad account.
    After authorization, they will be redirected back with an authorization code.
    """
    config = _get_platform_config(platform)
    if not config:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth not supported for platform: {platform}"
        )
    
    if not config["client_id"] or not config["client_secret"]:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth credentials not configured for {platform}"
        )
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "platform": platform,
        "user_id": user.id,
        "org_id": org.id,
        "created_at": datetime.utcnow(),
    }
    
    # Clean old states (older than 10 minutes)
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    expired = [k for k, v in _oauth_states.items() if v["created_at"] < cutoff]
    for k in expired:
        del _oauth_states[k]
    
    provider = get_oauth_provider(
        platform,
        config["client_id"],
        config["client_secret"],
        config["redirect_uri"],
    )
    
    url = provider.get_authorization_url(state, config.get("scope"))
    
    return OAuthURLResponse(url=url, state=state)


@router.post("/exchange", response_model=OAuthExchangeResponse)
async def exchange_oauth_code(
    payload: OAuthExchangeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """
    Exchange OAuth authorization code for access token and create connection.
    
    This endpoint handles the OAuth callback flow:
    1. Validates the state token (CSRF protection)
    2. Exchanges the authorization code for an access token
    3. Creates a new connection with the token
    """
    platform = payload.platform
    code = payload.code
    
    config = _get_platform_config(platform)
    if not config:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth not supported for platform: {platform}"
        )
    
    # Validate state if provided
    if payload.state:
        state_data = _oauth_states.get(payload.state)
        if not state_data:
            raise HTTPException(status_code=400, detail="Invalid or expired state token")
        if state_data["platform"] != platform:
            raise HTTPException(status_code=400, detail="Platform mismatch")
        if state_data["user_id"] != user.id:
            raise HTTPException(status_code=400, detail="User mismatch")
        # Remove used state
        del _oauth_states[payload.state]
    
    # Exchange code for token
    try:
        provider = get_oauth_provider(
            platform,
            config["client_id"],
            config["client_secret"],
            config["redirect_uri"],
        )
        token = await provider.exchange_code(code)
        await provider.close()
    except Exception as e:
        logger.exception(f"OAuth exchange failed for {platform}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange code: {str(e)}"
        )
    
    # Prepare credentials
    credentials = token.to_dict()
    if payload.account_id:
        credentials["account_id"] = payload.account_id
    
    # Encrypt credentials
    encrypted_creds = maybe_encrypt(credentials)
    
    # Create connection
    platform_enum = Platform(platform)
    connection = Connection(
        organization_id=org.id,
        platform=platform_enum,
        name=f"{platform.title()} (OAuth)",
        credentials_json=encrypted_creds,
        auto_sync_enabled=True,
        auto_sync_every_minutes=1440,  # Daily
        auto_sync_window_days=7,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    
    logger.info(f"Created OAuth connection {connection.id} for {platform}")
    
    return OAuthExchangeResponse(
        connection_id=connection.id,
        platform=platform,
        message=f"Successfully connected {platform.title()} account",
    )


@router.post("/ozon/apikey", response_model=OAuthExchangeResponse)
async def create_ozon_connection(
    client_id: str = Query(..., description="Ozon Client ID"),
    client_secret: str = Query(..., description="Ozon Client Secret"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
):
    """
    Create Ozon connection using API keys.
    
    Ozon Performance uses client credentials (API keys) instead of OAuth code flow.
    """
    # Validate credentials by trying to get a token
    try:
        provider = get_oauth_provider(
            "ozon",
            client_id,
            client_secret,
            "",  # No redirect URI for Ozon
        )
        token = await provider.exchange_code("")  # Gets client credentials token
        await provider.close()
    except Exception as e:
        logger.exception("Ozon API key validation failed")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Ozon credentials: {str(e)}"
        )
    
    # Store credentials
    credentials = {
        "client_id": client_id,
        "client_secret": client_secret,
        **token.to_dict(),
    }
    encrypted_creds = maybe_encrypt(credentials)
    
    connection = Connection(
        organization_id=org.id,
        platform=Platform.ozon,
        name="Ozon Performance",
        credentials_json=encrypted_creds,
        auto_sync_enabled=True,
        auto_sync_every_minutes=1440,
        auto_sync_window_days=7,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    
    return OAuthExchangeResponse(
        connection_id=connection.id,
        platform="ozon",
        message="Successfully connected Ozon Performance account",
    )
