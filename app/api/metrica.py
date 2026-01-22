"""
Yandex Metrica API Endpoints.

OAuth flow and data endpoints for Metrica integration.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

from app.api.deps import get_db, get_current_user, get_current_org_id
from app.db.models import User, Organization
from app.services.yandex_metrica import YandexMetricaService, get_metrica_service
from app.core.config import get_settings

router = APIRouter(prefix="/metrica", tags=["Yandex Metrica"])


# =============================================================================
# SCHEMAS
# =============================================================================

class MetricaAuthUrlResponse(BaseModel):
    """OAuth authorization URL response."""
    auth_url: str
    

class MetricaTokenExchangeRequest(BaseModel):
    """Request to exchange OAuth code for token."""
    code: str
    

class MetricaTokenResponse(BaseModel):
    """OAuth token response."""
    access_token: str
    expires_in: int
    connected: bool = True


class MetricaCounterResponse(BaseModel):
    """Metrica counter (site)."""
    id: int
    name: str
    site: str
    status: str
    

class MetricaGoalResponse(BaseModel):
    """Metrica goal."""
    id: int
    name: str
    type: str
    

class MetricaStatsRequest(BaseModel):
    """Request for statistics."""
    counter_id: int
    date_from: str  # YYYY-MM-DD
    date_to: str
    

class MetricaVisitStatsResponse(BaseModel):
    """Visit statistics response."""
    date: str
    visits: int
    page_views: int
    users: int
    bounce_rate: float
    avg_visit_duration: float


# =============================================================================
# OAUTH ENDPOINTS
# =============================================================================

@router.get("/auth-url", response_model=MetricaAuthUrlResponse)
def get_auth_url(
    state: str = Query(default=""),
    current_user: User = Depends(get_current_user),
):
    """
    Get OAuth authorization URL for Yandex Metrica.
    
    Redirect user to this URL to grant access.
    """
    settings = get_settings()
    if not settings.yandex_client_id:
        raise HTTPException(status_code=503, detail="Yandex OAuth is not configured")
    service = get_metrica_service()
    auth_url = service.get_authorization_url(state=state)
    return MetricaAuthUrlResponse(auth_url=auth_url)


@router.post("/connect", response_model=MetricaTokenResponse)
async def connect_metrica(
    payload: MetricaTokenExchangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """
    Exchange OAuth code for access token and save to organization.
    
    Called after user completes OAuth flow.
    """
    settings = get_settings()
    if not settings.yandex_client_id or not settings.yandex_client_secret:
        raise HTTPException(status_code=503, detail="Yandex OAuth is not configured")
    service = get_metrica_service()
    
    try:
        token_data = await service.exchange_code_for_token(payload.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
    
    # Store token in organization settings
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Save to org profile or dedicated table
    # For now, store in org metadata
    if not org.metadata_json:
        org.metadata_json = {}
    
    org.metadata_json["metrica_token"] = {
        "access_token": token_data["access_token"],
        "expires_in": token_data.get("expires_in", 0),
        "refresh_token": token_data.get("refresh_token"),
        "connected_at": datetime.utcnow().isoformat(),
    }
    db.commit()
    
    return MetricaTokenResponse(
        access_token=token_data["access_token"][:20] + "...",  # Masked
        expires_in=token_data.get("expires_in", 0),
        connected=True,
    )


@router.get("/status")
def get_metrica_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """Check if Metrica is connected for organization."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not org or not org.metadata_json:
        return {"connected": False}
    
    token_data = org.metadata_json.get("metrica_token")
    if not token_data:
        return {"connected": False}
    
    return {
        "connected": True,
        "connected_at": token_data.get("connected_at"),
    }


# =============================================================================
# DATA ENDPOINTS
# =============================================================================

@router.get("/counters", response_model=List[MetricaCounterResponse])
async def get_counters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """Get list of Metrica counters (sites) for connected account."""
    token = _get_org_token(db, org_id)
    service = get_metrica_service(access_token=token)
    
    try:
        counters = await service.get_counters()
        return [
            MetricaCounterResponse(
                id=c.id,
                name=c.name,
                site=c.site,
                status=c.status,
            )
            for c in counters
        ]
    finally:
        await service.close()


@router.get("/counters/{counter_id}/goals", response_model=List[MetricaGoalResponse])
async def get_goals(
    counter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """Get goals (conversions) for a counter."""
    token = _get_org_token(db, org_id)
    service = get_metrica_service(access_token=token)
    
    try:
        goals = await service.get_goals(counter_id)
        return [
            MetricaGoalResponse(
                id=g.id,
                name=g.name,
                type=g.type,
            )
            for g in goals
        ]
    finally:
        await service.close()


@router.post("/stats", response_model=List[MetricaVisitStatsResponse])
async def get_stats(
    payload: MetricaStatsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """Get visit statistics for a counter."""
    token = _get_org_token(db, org_id)
    service = get_metrica_service(access_token=token)
    
    try:
        stats = await service.get_visits_stats(
            counter_id=payload.counter_id,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        return [
            MetricaVisitStatsResponse(
                date=s.date,
                visits=s.visits,
                page_views=s.page_views,
                users=s.users,
                bounce_rate=s.bounce_rate,
                avg_visit_duration=s.avg_visit_duration,
            )
            for s in stats
        ]
    finally:
        await service.close()


@router.get("/attribution/{counter_id}")
async def get_attribution(
    counter_id: int,
    date_from: str = Query(...),
    date_to: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """Get attribution report by traffic source."""
    token = _get_org_token(db, org_id)
    service = get_metrica_service(access_token=token)
    
    try:
        report = await service.get_attribution_report(
            counter_id=counter_id,
            date_from=date_from,
            date_to=date_to,
        )
        return report
    finally:
        await service.close()


# =============================================================================
# HELPERS
# =============================================================================

def _get_org_token(db: Session, org_id: int) -> str:
    """Get Metrica access token for organization."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not org or not org.metadata_json:
        raise HTTPException(status_code=400, detail="Metrica not connected")
    
    token_data = org.metadata_json.get("metrica_token")
    if not token_data or not token_data.get("access_token"):
        raise HTTPException(status_code=400, detail="Metrica not connected")
    
    return token_data["access_token"]
