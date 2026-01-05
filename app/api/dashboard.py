from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas import DashboardSummaryResponse, DashboardTotals, DashboardDailyItem
from app.db.models import Connection, MetricSnapshot
from app.db.session import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    advertiser_id: int = Query(..., gt=0),
    date_from: date = Query(...),
    date_to: date = Query(...),
    session: Session = Depends(get_db),
):
    base_query = (
        session.query(MetricSnapshot)
        .join(Connection, Connection.id == MetricSnapshot.connection_id)
        .filter(
            Connection.advertiser_id == advertiser_id,
            MetricSnapshot.date >= date_from,
            MetricSnapshot.date <= date_to,
            MetricSnapshot.level == "campaign",
        )
    )

    totals_row = (
        base_query.with_entities(
            func.coalesce(func.sum(MetricSnapshot.impressions), 0),
            func.coalesce(func.sum(MetricSnapshot.clicks), 0),
            func.coalesce(func.sum(MetricSnapshot.spend), 0),
            func.coalesce(func.sum(MetricSnapshot.leads), 0),
            func.coalesce(func.sum(MetricSnapshot.purchases), 0),
            func.coalesce(func.sum(MetricSnapshot.revenue), 0),
        )
        .first()
    )

    totals = DashboardTotals(
        impressions=int(totals_row[0]),
        clicks=int(totals_row[1]),
        spend=int(totals_row[2]),
        leads=int(totals_row[3]),
        purchases=int(totals_row[4]),
        revenue=int(totals_row[5]),
    )

    daily_rows = (
        base_query.with_entities(
            MetricSnapshot.date,
            func.coalesce(func.sum(MetricSnapshot.impressions), 0),
            func.coalesce(func.sum(MetricSnapshot.clicks), 0),
            func.coalesce(func.sum(MetricSnapshot.spend), 0),
            func.coalesce(func.sum(MetricSnapshot.leads), 0),
            func.coalesce(func.sum(MetricSnapshot.purchases), 0),
            func.coalesce(func.sum(MetricSnapshot.revenue), 0),
        )
        .group_by(MetricSnapshot.date)
        .order_by(MetricSnapshot.date)
        .all()
    )

    daily = [
        DashboardDailyItem(
            date=row[0],
            impressions=int(row[1]),
            clicks=int(row[2]),
            spend=int(row[3]),
            leads=int(row[4]),
            purchases=int(row[5]),
            revenue=int(row[6]),
        )
        for row in daily_rows
    ]

    return DashboardSummaryResponse(
        advertiser_id=advertiser_id,
        date_from=date_from,
        date_to=date_to,
        totals=totals,
        daily=daily,
    )
