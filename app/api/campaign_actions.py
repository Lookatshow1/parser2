"""
Campaign Actions API

Endpoints for performing actions on campaigns from the UI:
- Pause/Enable campaigns
- Pause/Enable ads  
- Change bids (future)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.db.models import Connection, Platform, AdCampaign
from app.security.auth import verify_password
from app.api.deps import get_current_user_id
from app.security.org_context import validate_org_access
from app.services.connector_service import get_connector
from app.security.credentials_crypto import maybe_decrypt
from app.services.audit import log_org_event

router = APIRouter(prefix="/api/campaigns", tags=["campaign-actions"])


class CampaignActionRequest(BaseModel):
    connection_id: int


class AdActionRequest(BaseModel):
    connection_id: int
    ad_id: str | int


class BidActionRequest(BaseModel):
    connection_id: int
    ad_id: str | int
    bid: float


class ActionResponse(BaseModel):
    success: bool
    message: str
    details: dict = {}


def _get_connection_and_connector(db: Session, connection_id: int, org_id: int):
    """Helper to get connection and build connector."""
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    if connection.organization_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    creds = maybe_decrypt(connection.credentials_json) if connection.credentials_json else {}
    connector = get_connector(connection.platform, creds)
    
    return connection, connector


@router.post("/{campaign_id}/pause", response_model=ActionResponse)
def pause_campaign(
    campaign_id: int,
    payload: CampaignActionRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Pause a campaign in the advertising platform."""
    org_id = validate_org_access(db, current_user_id)
    connection, connector = _get_connection_and_connector(db, payload.connection_id, org_id)
    
    # Get external campaign ID
    campaign = db.query(AdCampaign).filter(AdCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    external_id = campaign.external_id or str(campaign_id)
    
    if not hasattr(connector, "pause_campaign"):
        raise HTTPException(status_code=400, detail="Platform doesn't support pause_campaign")
    
    result = connector.pause_campaign(external_id)
    
    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=current_user_id,
        action="campaign_paused",
        subject_type="campaign",
        subject_id=campaign_id,
        meta={"result": result},
    )
    db.commit()
    
    return ActionResponse(
        success=result.get("success", False),
        message="Campaign paused" if result.get("success") else result.get("error", "Failed"),
        details=result,
    )


@router.post("/{campaign_id}/enable", response_model=ActionResponse)
def enable_campaign(
    campaign_id: int,
    payload: CampaignActionRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Enable a paused campaign in the advertising platform."""
    org_id = validate_org_access(db, current_user_id)
    connection, connector = _get_connection_and_connector(db, payload.connection_id, org_id)
    
    campaign = db.query(AdCampaign).filter(AdCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    external_id = campaign.external_id or str(campaign_id)
    
    if not hasattr(connector, "enable_campaign"):
        raise HTTPException(status_code=400, detail="Platform doesn't support enable_campaign")
    
    result = connector.enable_campaign(external_id)
    
    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=current_user_id,
        action="campaign_enabled",
        subject_type="campaign",
        subject_id=campaign_id,
        meta={"result": result},
    )
    db.commit()
    
    return ActionResponse(
        success=result.get("success", False),
        message="Campaign enabled" if result.get("success") else result.get("error", "Failed"),
        details=result,
    )


@router.post("/{campaign_id}/ads/{ad_id}/pause", response_model=ActionResponse)
def pause_ad(
    campaign_id: int,
    ad_id: str,
    payload: CampaignActionRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Pause a specific ad in the advertising platform."""
    org_id = validate_org_access(db, current_user_id)
    connection, connector = _get_connection_and_connector(db, payload.connection_id, org_id)
    
    if not hasattr(connector, "pause_ad"):
        raise HTTPException(status_code=400, detail="Platform doesn't support pause_ad")
    
    result = connector.pause_ad(ad_id)
    
    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=current_user_id,
        action="ad_paused",
        subject_type="ad",
        subject_id=int(ad_id) if ad_id.isdigit() else None,
        meta={"campaign_id": campaign_id, "ad_id": ad_id, "result": result},
    )
    db.commit()
    
    return ActionResponse(
        success=result.get("success", False),
        message="Ad paused" if result.get("success") else result.get("error", "Failed"),
        details=result,
    )


@router.post("/{campaign_id}/ads/{ad_id}/enable", response_model=ActionResponse)
def enable_ad(
    campaign_id: int,
    ad_id: str,
    payload: CampaignActionRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Enable a paused ad in the advertising platform."""
    org_id = validate_org_access(db, current_user_id)
    connection, connector = _get_connection_and_connector(db, payload.connection_id, org_id)
    
    if not hasattr(connector, "enable_ad"):
        raise HTTPException(status_code=400, detail="Platform doesn't support enable_ad")
    
    result = connector.enable_ad(ad_id)
    
    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=current_user_id,
        action="ad_enabled",
        subject_type="ad",
        subject_id=int(ad_id) if ad_id.isdigit() else None,
        meta={"campaign_id": campaign_id, "ad_id": ad_id, "result": result},
    )
    db.commit()
    
    return ActionResponse(
        success=result.get("success", False),
        message="Ad enabled" if result.get("success") else result.get("error", "Failed"),
        details=result,
    )


@router.post("/{campaign_id}/ads/{ad_id}/set-bid", response_model=ActionResponse)
def set_ad_bid(
    campaign_id: int,
    ad_id: str,
    payload: BidActionRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """Set bid for an ad in the advertising platform."""
    org_id = validate_org_access(db, current_user_id)
    connection, connector = _get_connection_and_connector(db, payload.connection_id, org_id)
    
    if not hasattr(connector, "set_bid"):
        raise HTTPException(status_code=400, detail="Platform doesn't support set_bid")
    
    result = connector.set_bid(ad_id, payload.bid)
    
    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=current_user_id,
        action="ad_bid_changed",
        subject_type="ad",
        subject_id=int(ad_id) if ad_id.isdigit() else None,
        meta={"campaign_id": campaign_id, "ad_id": ad_id, "bid": payload.bid, "result": result},
    )
    db.commit()
    
    return ActionResponse(
        success=result.get("success", False),
        message=f"Bid set to {payload.bid}" if result.get("success") else result.get("error", "Failed"),
        details=result,
    )
