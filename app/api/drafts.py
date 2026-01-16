from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.db.models import User
from app.db.models_drafts import DraftCampaign, DraftAdGroup, DraftAd
from app.api.drafts_schemas import DraftCampaignResponse, DraftCampaignCreate

router = APIRouter(prefix="/drafts", tags=["Drafts"])

@router.get("/", response_model=List[DraftCampaignResponse])
def list_drafts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # TODO: Filter by organization_id
    # Assuming user has org context or we fetch all for their orgs
    # Simplified: Get all drafts for now
    return db.query(DraftCampaign).offset(skip).limit(limit).all()

@router.get("/{id}", response_model=DraftCampaignResponse)
def get_draft(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    draft = db.query(DraftCampaign).filter(DraftCampaign.id == id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@router.delete("/{id}")
def delete_draft(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    draft = db.query(DraftCampaign).filter(DraftCampaign.id == id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    db.commit()
    return {"ok": True}

@router.post("/{id}/publish")
async def publish_draft(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.integrations import IntegrationService
    service = IntegrationService(db)
    try:
        external_id = await service.publish_draft(id)
        return {"ok": True, "external_id": external_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

