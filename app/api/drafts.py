from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_membership, get_current_org, get_current_user
from app.db.models import Organization, User, Connection
from app.db.models_drafts import DraftCampaign, DraftAdGroup, DraftAd
from app.api.drafts_schemas import DraftCampaignResponse, DraftCampaignCreate
from app.services.rbac import can_read_campaigns, can_write_campaigns

router = APIRouter(prefix="/drafts", tags=["Drafts"])

def _require_read(role: str) -> None:
    if not can_read_campaigns(role):
        raise HTTPException(status_code=403, detail="Недостаточно прав")


def _require_write(role: str) -> None:
    if not can_write_campaigns(role):
        raise HTTPException(status_code=403, detail="Недостаточно прав")

@router.get("/", response_model=List[DraftCampaignResponse])
def list_drafts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    return (
        db.query(DraftCampaign)
        .filter(DraftCampaign.organization_id == org.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

@router.get("/{id}", response_model=DraftCampaignResponse)
def get_draft(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    draft = (
        db.query(DraftCampaign)
        .filter(DraftCampaign.id == id, DraftCampaign.organization_id == org.id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@router.delete("/{id}")
def delete_draft(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    draft = (
        db.query(DraftCampaign)
        .filter(DraftCampaign.id == id, DraftCampaign.organization_id == org.id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    db.delete(draft)
    db.commit()
    return {"ok": True}

@router.post("/{id}/publish")
async def publish_draft(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    from app.services.integrations import IntegrationService
    draft = (
        db.query(DraftCampaign)
        .filter(DraftCampaign.id == id, DraftCampaign.organization_id == org.id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    service = IntegrationService(db)
    try:
        external_id = await service.publish_draft(draft.id)
        return {"ok": True, "external_id": external_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Ad Group & Ad Editing ---

from pydantic import BaseModel
from typing import Optional

class AdGroupUpdate(BaseModel):
    name: Optional[str] = None

class AdUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    landing_url: Optional[str] = None


class DraftCampaignUpdate(BaseModel):
    connection_id: Optional[int] = None
    budget_daily: Optional[float] = None
    landing_url: Optional[str] = None
    product_ids: Optional[List[int]] = None

@router.patch("/groups/{group_id}")
def update_ad_group(
    group_id: int,
    payload: AdGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    group = (
        db.query(DraftAdGroup)
        .join(DraftCampaign, DraftCampaign.id == DraftAdGroup.campaign_id)
        .filter(DraftAdGroup.id == group_id, DraftCampaign.organization_id == org.id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Ad group not found")
    
    if payload.name is not None:
        group.name = payload.name
    
    db.commit()
    return {"ok": True, "id": group.id, "name": group.name}

@router.patch("/ads/{ad_id}")
def update_ad(
    ad_id: int,
    payload: AdUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    ad = (
        db.query(DraftAd)
        .join(DraftAdGroup, DraftAdGroup.id == DraftAd.ad_group_id)
        .join(DraftCampaign, DraftCampaign.id == DraftAdGroup.campaign_id)
        .filter(DraftAd.id == ad_id, DraftCampaign.organization_id == org.id)
        .first()
    )
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    if payload.title is not None:
        ad.title = payload.title
    if payload.text is not None:
        ad.text = payload.text
    if payload.landing_url is not None:
        ad.landing_url = payload.landing_url
    
    db.commit()
    return {"ok": True, "id": ad.id, "title": ad.title, "text": ad.text}


@router.patch("/{id}")
def update_draft(
    id: int,
    payload: DraftCampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    draft = (
        db.query(DraftCampaign)
        .filter(DraftCampaign.id == id, DraftCampaign.organization_id == org.id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if payload.connection_id is not None:
        connection = (
            db.query(Connection)
            .filter(Connection.id == payload.connection_id, Connection.organization_id == org.id)
            .first()
        )
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        draft.connection_id = connection.id
        draft.platform = connection.platform.value if hasattr(connection.platform, "value") else str(connection.platform)

    payload_json = draft.payload_json or {}
    if payload.budget_daily is not None:
        payload_json["budget"] = payload.budget_daily
    if payload.landing_url is not None:
        payload_json["landing_url"] = payload.landing_url
    if payload.product_ids is not None:
        payload_json["product_ids"] = payload.product_ids

    draft.payload_json = payload_json
    db.commit()

    return {"ok": True, "id": draft.id}
