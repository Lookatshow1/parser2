"""
Analytics API Endpoints
"""
from datetime import date, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.api.deps import get_current_org_id
from app.services.analytics import AnalyticsService
from pydantic import BaseModel


router = APIRouter(prefix="/analytics", tags=["Analytics"])


class MetricsSummary(BaseModel):
    impressions: int
    clicks: int
    spend: float
    conversions: int
    revenue: float
    ctr: float
    cpc: float
    conversion_rate: float
    roas: float


class TimeseriesPoint(BaseModel):
    date: str
    value: float


class PlatformMetrics(BaseModel):
    platform: str
    impressions: int
    clicks: int
    spend: float
    conversions: int
    revenue: float
    ctr: float
    roas: float


class PeriodComparison(BaseModel):
    current: MetricsSummary
    previous: MetricsSummary
    changes: dict


@router.get("/summary", response_model=MetricsSummary)
async def get_summary(
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    platform: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
    org_id: int = Depends(get_current_org_id)
):
    """Получить сводку метрик за период."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()
    
    service = AnalyticsService(session)
    return await service.get_dashboard_metrics(org_id, date_from, date_to, platform)


@router.get("/timeseries", response_model=List[TimeseriesPoint])
async def get_timeseries(
    metric: str = Query(default="impressions"),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    platform: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
    org_id: int = Depends(get_current_org_id)
):
    """Получить временной ряд метрики."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()
    
    service = AnalyticsService(session)
    return await service.get_metrics_timeseries(org_id, date_from, date_to, metric, platform)


@router.get("/platforms", response_model=List[PlatformMetrics])
async def get_platform_breakdown(
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    session: AsyncSession = Depends(get_session),
    org_id: int = Depends(get_current_org_id)
):
    """Получить разбивку метрик по платформам."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()
    
    service = AnalyticsService(session)
    return await service.get_platform_breakdown(org_id, date_from, date_to)


@router.get("/compare", response_model=PeriodComparison)
async def compare_periods(
    session: AsyncSession = Depends(get_session),
    org_id: int = Depends(get_current_org_id)
):
    """Сравнить текущую неделю с предыдущей."""
    today = date.today()
    
    current_from = today - timedelta(days=7)
    current_to = today
    previous_from = today - timedelta(days=14)
    previous_to = today - timedelta(days=7)
    
    service = AnalyticsService(session)
    return await service.compare_periods(org_id, current_from, current_to, previous_from, previous_to)


@router.post("/seed-demo")
async def seed_demo_data(
    session: AsyncSession = Depends(get_session),
    org_id: int = Depends(get_current_org_id)
):
    """Создать демо-данные аналитики."""
    service = AnalyticsService(session)
    await service.seed_demo_data(org_id)
    return {"message": "Демо-данные созданы"}
