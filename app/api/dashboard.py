from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_org
from app.db.models import Organization
from app.db.session import get_db
from app.api.schemas import UnifiedDashboardResponse, DashboardChannel
from app.services.dashboard_unified_service import get_unified_timeseries, get_dashboard_channels

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/unified-timeseries", response_model=UnifiedDashboardResponse)
def unified_timeseries(
    date_from: date,
    date_to: date,
    channel: str = "all",
    connection_ids: str | None = Query(None),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    c_ids = None
    if connection_ids:
        try:
            c_ids = [int(x) for x in connection_ids.split(",") if x.strip()]
        except ValueError:
            pass # Ignore invalid

    return get_unified_timeseries(db, org.id, date_from, date_to, channel, c_ids)

@router.get("/channels", response_model=list[DashboardChannel])
def list_channels(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    return get_dashboard_channels(db, org.id)
