from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas import DashboardSummaryResponse, DashboardTotals, DashboardDailyItem
from app.api.deps import get_current_org, get_current_user
from app.db.models import MetricSnapshot, Organization, User
from app.db.session import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

def _safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _calc_efficiency(
    impressions: int,
    clicks: int,
    spend: int,
    purchases: int,
    revenue: int,
) -> dict[str, float | None]:
    ctr = _safe_div(clicks, impressions)
    cpc = _safe_div(spend, clicks)
    cpm = _safe_div(spend * 1000, impressions)
    cpa = _safe_div(spend, purchases)
    roas = _safe_div(revenue, spend)
    return {
        "ctr": round(ctr, 4) if ctr is not None else None,
        "cpc": round(cpc, 2) if cpc is not None else None,
        "cpm": round(cpm, 2) if cpm is not None else None,
        "cpa": round(cpa, 2) if cpa is not None else None,
        "roas": round(roas, 4) if roas is not None else None,
    }


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    connection_id: int | None = Query(None, gt=0),
    date_from: date = Query(...),
    date_to: date = Query(...),
    session: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    base_query = (
        session.query(MetricSnapshot)
        .filter(
            MetricSnapshot.organization_id == org.id,
            MetricSnapshot.date >= date_from,
            MetricSnapshot.date <= date_to,
            MetricSnapshot.level == "campaign",
        )
    )
    if connection_id is not None:
        base_query = base_query.filter(MetricSnapshot.connection_id == connection_id)
    else:
        base_query = base_query.filter(MetricSnapshot.connection_id.isnot(None))

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

    totals_eff = _calc_efficiency(
        impressions=int(totals_row[0]),
        clicks=int(totals_row[1]),
        spend=int(totals_row[2]),
        purchases=int(totals_row[4]),
        revenue=int(totals_row[5]),
    )
    totals = DashboardTotals(
        impressions=int(totals_row[0]),
        clicks=int(totals_row[1]),
        spend=int(totals_row[2]),
        leads=int(totals_row[3]),
        purchases=int(totals_row[4]),
        revenue=int(totals_row[5]),
        **totals_eff,
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

    daily = []
    for row in daily_rows:
        daily_eff = _calc_efficiency(
            impressions=int(row[1]),
            clicks=int(row[2]),
            spend=int(row[3]),
            purchases=int(row[5]),
            revenue=int(row[6]),
        )
        daily.append(
            DashboardDailyItem(
                date=row[0],
                impressions=int(row[1]),
                clicks=int(row[2]),
                spend=int(row[3]),
                leads=int(row[4]),
                purchases=int(row[5]),
                revenue=int(row[6]),
                **daily_eff,
            )
        )

    connections_summary = None
    if connection_id is None:
        connection_rows = (
            base_query.with_entities(
                MetricSnapshot.connection_id,
                func.coalesce(func.sum(MetricSnapshot.impressions), 0),
                func.coalesce(func.sum(MetricSnapshot.clicks), 0),
                func.coalesce(func.sum(MetricSnapshot.spend), 0),
                func.coalesce(func.sum(MetricSnapshot.leads), 0),
                func.coalesce(func.sum(MetricSnapshot.purchases), 0),
                func.coalesce(func.sum(MetricSnapshot.revenue), 0),
            )
            .filter(MetricSnapshot.connection_id.isnot(None))
            .group_by(MetricSnapshot.connection_id)
            .order_by(MetricSnapshot.connection_id)
            .all()
        )
        connections_summary = []
        for row in connection_rows:
            conn_eff = _calc_efficiency(
                impressions=int(row[1]),
                clicks=int(row[2]),
                spend=int(row[3]),
                purchases=int(row[5]),
                revenue=int(row[6]),
            )
            connections_summary.append(
                {
                    "connection_id": row[0],
                    "totals": {
                        "impressions": int(row[1]),
                        "clicks": int(row[2]),
                        "spend": int(row[3]),
                        "leads": int(row[4]),
                        "purchases": int(row[5]),
                        "revenue": int(row[6]),
                        **conn_eff,
                    },
                }
            )

    return DashboardSummaryResponse(
        connection_id=connection_id,
        date_from=date_from,
        date_to=date_to,
        totals=totals,
        daily=daily,
        connections=connections_summary,
    )
