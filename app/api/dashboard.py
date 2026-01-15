from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_current_org
from app.db.models import Connection, MetricSnapshot, Organization
from app.db.session import get_db
from app.api.schemas import (
    UnifiedDashboardResponse,
    DashboardChannel,
    DashboardSummaryResponse,
    DashboardTotals,
    DashboardDailyItem,
    DashboardConnectionTotals,
    KpiTimeseriesResponse,
    KpiSummaryResponse
)
from app.services.dashboard_unified_service import get_unified_timeseries, get_dashboard_channels
from app.services.dashboard_service import build_kpi_timeseries, build_kpi_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _calc_totals(
    impressions: int,
    clicks: int,
    spend: int,
    leads: int,
    purchases: int,
    revenue: int,
) -> DashboardTotals:
    ctr = _safe_div(clicks, impressions)
    cpc = _safe_div(spend, clicks)
    cpm = _safe_div(spend * 1000, impressions)
    cpa = _safe_div(spend, purchases)
    roas = _safe_div(revenue, spend)
    return DashboardTotals(
        impressions=impressions,
        clicks=clicks,
        spend=spend,
        leads=leads,
        purchases=purchases,
        revenue=revenue,
        ctr=round(ctr, 4) if ctr is not None else None,
        cpc=round(cpc, 2) if cpc is not None else None,
        cpm=round(cpm, 2) if cpm is not None else None,
        cpa=round(cpa, 2) if cpa is not None else None,
        roas=round(roas, 4) if roas is not None else None,
    )

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


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    date_from: date = Query(..., description="Начало периода (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Конец периода (YYYY-MM-DD)"),
    connection_id: int | None = Query(None, description="ID подключения"),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="Дата начала не может быть позже даты окончания")

    if (date_to - date_from).days > 366:
        raise HTTPException(status_code=400, detail="Диапазон дат не должен превышать 366 дней")

    if connection_id:
        conn = db.query(Connection).filter(
            Connection.id == connection_id,
            Connection.organization_id == org.id,
        ).first()
        if not conn:
            raise HTTPException(status_code=404, detail="Подключение не найдено")
        connection_ids = [connection_id]
    else:
        connection_ids = db.query(Connection.id).filter(Connection.organization_id == org.id).all()
        connection_ids = [row[0] for row in connection_ids]

    if not connection_ids:
        return DashboardSummaryResponse(
            connection_id=connection_id,
            date_from=date_from,
            date_to=date_to,
            totals=_calc_totals(0, 0, 0, 0, 0, 0),
            daily=[],
            connections=[],
        )

    base_query = (
        db.query(
            MetricSnapshot.date,
            func.sum(MetricSnapshot.impressions).label("impressions"),
            func.sum(MetricSnapshot.clicks).label("clicks"),
            func.sum(MetricSnapshot.spend).label("spend"),
            func.sum(MetricSnapshot.leads).label("leads"),
            func.sum(MetricSnapshot.purchases).label("purchases"),
            func.sum(MetricSnapshot.revenue).label("revenue"),
        )
        .filter(MetricSnapshot.organization_id == org.id)
        .filter(MetricSnapshot.connection_id.in_(connection_ids))
        .filter(MetricSnapshot.date >= date_from)
        .filter(MetricSnapshot.date <= date_to)
        .filter(MetricSnapshot.level == "campaign")
        .group_by(MetricSnapshot.date)
        .order_by(MetricSnapshot.date)
    )

    daily_items: list[DashboardDailyItem] = []
    totals_impressions = totals_clicks = totals_spend = totals_leads = totals_purchases = totals_revenue = 0

    for row in base_query.all():
        impressions = int(row.impressions or 0)
        clicks = int(row.clicks or 0)
        spend = int(row.spend or 0)
        leads = int(row.leads or 0)
        purchases = int(row.purchases or 0)
        revenue = int(row.revenue or 0)

        totals_impressions += impressions
        totals_clicks += clicks
        totals_spend += spend
        totals_leads += leads
        totals_purchases += purchases
        totals_revenue += revenue

        daily_totals = _calc_totals(
            impressions,
            clicks,
            spend,
            leads,
            purchases,
            revenue,
        )
        daily_items.append(
            DashboardDailyItem(
                date=row.date,
                impressions=daily_totals.impressions,
                clicks=daily_totals.clicks,
                spend=daily_totals.spend,
                leads=daily_totals.leads,
                purchases=daily_totals.purchases,
                revenue=daily_totals.revenue,
                ctr=daily_totals.ctr,
                cpc=daily_totals.cpc,
                cpm=daily_totals.cpm,
                cpa=daily_totals.cpa,
                roas=daily_totals.roas,
            )
        )

    totals = _calc_totals(
        totals_impressions,
        totals_clicks,
        totals_spend,
        totals_leads,
        totals_purchases,
        totals_revenue,
    )

    connections_payload: list[DashboardConnectionTotals] | None = None
    if connection_id is None:
        connections_payload = []
        conn_rows = (
            db.query(
                MetricSnapshot.connection_id,
                func.sum(MetricSnapshot.impressions).label("impressions"),
                func.sum(MetricSnapshot.clicks).label("clicks"),
                func.sum(MetricSnapshot.spend).label("spend"),
                func.sum(MetricSnapshot.leads).label("leads"),
                func.sum(MetricSnapshot.purchases).label("purchases"),
                func.sum(MetricSnapshot.revenue).label("revenue"),
            )
            .filter(MetricSnapshot.organization_id == org.id)
            .filter(MetricSnapshot.connection_id.in_(connection_ids))
            .filter(MetricSnapshot.date >= date_from)
            .filter(MetricSnapshot.date <= date_to)
            .filter(MetricSnapshot.level == "campaign")
            .group_by(MetricSnapshot.connection_id)
        ).all()

        for row in conn_rows:
            connections_payload.append(
                DashboardConnectionTotals(
                    connection_id=row.connection_id,
                    totals=_calc_totals(
                        int(row.impressions or 0),
                        int(row.clicks or 0),
                        int(row.spend or 0),
                        int(row.leads or 0),
                        int(row.purchases or 0),
                        int(row.revenue or 0),
                    ),
                )
            )

    return DashboardSummaryResponse(
        connection_id=connection_id,
        date_from=date_from,
        date_to=date_to,
        totals=totals,
        daily=daily_items,
        connections=connections_payload,
    )

# --- KPI Dashboard Endpoints ---

@router.get("/kpi-timeseries", response_model=KpiTimeseriesResponse)
def kpi_timeseries(
    date_from: date = Query(..., description="Начало периода (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Конец периода (YYYY-MM-DD)"),
    connection_ids: Optional[str] = Query(None, description="Список ID подключений через запятую"),
    platform: Optional[str] = Query(None, description="Платформа: yandex, vk, ozon"),
    mode: str = Query("index", regex="^(index|absolute)$", description="Режим: index (индексы 0-100) или absolute (абсолютные значения)"),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Получить таймсерию KPI метрик с нормализацией"""
    # Validate date range
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="Дата начала не может быть позже даты окончания")
    
    if (date_to - date_from).days > 366:
        raise HTTPException(status_code=400, detail="Диапазон дат не должен превышать 366 дней")
    
    # Parse connection_ids
    conn_ids = None
    if connection_ids:
        try:
            conn_ids = [int(x.strip()) for x in connection_ids.split(",") if x.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректный формат connection_ids")
    
    return build_kpi_timeseries(
        db=db,
        org_id=org.id,
        date_from=date_from,
        date_to=date_to,
        connection_ids=conn_ids,
        platform=platform,
        mode=mode
    )


@router.get("/kpi-summary", response_model=KpiSummaryResponse)
def kpi_summary(
    date_from: date = Query(..., description="Начало периода (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Конец периода (YYYY-MM-DD)"),
    connection_ids: Optional[str] = Query(None, description="Список ID подключений через запятую"),
    platform: Optional[str] = Query(None, description="Платформа: yandex, vk, ozon"),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Получить сводку KPI для карточек"""
    # Validate date range
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="Дата начала не может быть позже даты окончания")
    
    if (date_to - date_from).days > 366:
        raise HTTPException(status_code=400, detail="Диапазон дат не должен превышать 366 дней")
    
    # Parse connection_ids
    conn_ids = None
    if connection_ids:
        try:
            conn_ids = [int(x.strip()) for x in connection_ids.split(",") if x.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректный формат connection_ids")
    
    return build_kpi_summary(
        db=db,
        org_id=org.id,
        date_from=date_from,
        date_to=date_to,
        connection_ids=conn_ids,
        platform=platform
    )
