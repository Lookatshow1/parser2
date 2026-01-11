from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_org, get_current_user
from app.db.models import Organization, User, OrgRecommendation, AdCampaign
from app.db.session import get_db
from app.services.recommendations_service import compute_recommendations_for_org, resolve_recommendation
from pydantic import BaseModel

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

class RecommendationOut(BaseModel):
    id: int
    organization_id: int
    connection_id: int | None = None
    subject_type: str
    subject_id: int | None = None
    subject_name: str | None = None
    code: str
    severity: str
    title: str
    description: str
    action: str
    meta_json: dict
    valid_from: date
    valid_to: date
    created_at: str
    resolved_at: str | None = None

    class Config:
        from_attributes = True

class RecommendationListResponse(BaseModel):
    items: list[RecommendationOut]
    total: int

class RecomputeRequest(BaseModel):
    date_from: date
    date_to: date
    connection_ids: list[int] | None = None

@router.get("", response_model=RecommendationListResponse)
def list_recommendations(
    date_from: date = Query(..., description="Начало периода"),
    date_to: date = Query(..., description="Конец периода"),
    connection_id: int | None = Query(None),
    severity: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    q = db.query(OrgRecommendation).filter(
        OrgRecommendation.organization_id == org.id,
        OrgRecommendation.valid_from <= date_to,
        OrgRecommendation.valid_to >= date_from,
        OrgRecommendation.resolved_at.is_(None) # Show only unresolved by default? Or filter?
        # Usually we show active recommendations.
        # Let's show all matching period, UI can filter resolved.
        # But typically "Recommendations" list implies "To Do".
        # Let's filter resolved_at IS NULL by default unless flag?
        # Spec didn't say. Let's return all for history, UI can filter.
    )

    if connection_id:
        q = q.filter(OrgRecommendation.connection_id == connection_id)
    if severity:
        q = q.filter(OrgRecommendation.severity == severity)

    total = q.count()
    items = q.order_by(desc(OrgRecommendation.created_at)).limit(limit).offset(offset).all()

    # Enrich with subject names
    # Collect subject_ids for campaigns
    camp_ids = [i.subject_id for i in items if i.subject_type == "campaign" and i.subject_id]
    camp_names = {}
    if camp_ids:
        camps = db.query(AdCampaign.id, AdCampaign.name).filter(AdCampaign.id.in_(camp_ids)).all()
        camp_names = {c.id: c.name for c in camps}

    res_items = []
    for i in items:
        name = None
        if i.subject_type == "campaign":
            name = camp_names.get(i.subject_id)
        elif i.subject_type == "connection":
            # Connection name is not fetched here to avoid N+1, but could be joined.
            # For MVP, let's skip or fetch if needed.
            # Or just return None and let UI handle (UI has connection list).
            pass

        # Convert to Pydantic
        # created_at/resolved_at to string
        item_dict = {
            "id": i.id,
            "organization_id": i.organization_id,
            "connection_id": i.connection_id,
            "subject_type": i.subject_type,
            "subject_id": i.subject_id,
            "subject_name": name,
            "code": i.code,
            "severity": i.severity,
            "title": i.title,
            "description": i.description,
            "action": i.action,
            "meta_json": i.meta_json,
            "valid_from": i.valid_from,
            "valid_to": i.valid_to,
            "created_at": i.created_at.isoformat(),
            "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None
        }
        res_items.append(RecommendationOut(**item_dict))

    return {"items": res_items, "total": total}

@router.post("/recompute")
def recompute_recommendations(
    body: RecomputeRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    # Synchronous for MVP, but ideally async
    created, updated = compute_recommendations_for_org(
        db, org.id, body.date_from, body.date_to, body.connection_ids
    )
    return {"status": "ok", "created": created, "updated": updated}

@router.post("/{reco_id}/resolve")
def resolve_reco(
    reco_id: int,
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ok = resolve_recommendation(db, org.id, reco_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Рекомендация не найдена")
    return {"status": "resolved"}
