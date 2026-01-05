from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas import MetricAggregateResponse, MetricsSummaryResponse
from app.db.models import MetricSnapshot
from app.db.session import get_db
from app.services.metrics_service import get_connection_metrics

router = APIRouter(prefix="/metrics")


@router.get("", response_model=MetricAggregateResponse)
def metrics_by_connection(
    connection_id: int = Query(..., description="ID подключения"),
    date_from: date = Query(..., description="Начало периода"),
    date_to: date = Query(..., description="Конец периода"),
    group_by: str = Query("day", regex="^(day|campaign|day_campaign)$"),
    campaign_external_id: str | None = Query(None),
    session: Session = Depends(get_db),
):
    items = get_connection_metrics(
        session,
        connection_id=connection_id,
        date_from=date_from,
        date_to=date_to,
        group_by=group_by,
        campaign_external_id=campaign_external_id,
    )
    return {"items": items}


@router.get("/summary", response_model=MetricsSummaryResponse)
def metrics_summary(
    plan_id: int = Query(..., description="ID плана кампании"),
    date_from: date | None = Query(None, description="Начало периода (по умолчанию: 7 дней назад)"),
    date_to: date | None = Query(None, description="Конец периода (по умолчанию: сегодня UTC)"),
    session: Session = Depends(get_db),
):
    # Устанавливаем дефолтные значения дат (последние 7 дней)
    if date_to is None:
        date_to = datetime.utcnow().date()
    if date_from is None:
        date_from = date_to - timedelta(days=7)

    # Запрос с фильтрами по plan_id и датам
    query = (
        session.query(
            func.sum(MetricSnapshot.impressions).label("impressions_sum"),
            func.sum(MetricSnapshot.clicks).label("clicks_sum"),
            func.sum(MetricSnapshot.spend).label("spend_sum"),
            func.sum(MetricSnapshot.leads).label("leads_sum"),
            func.sum(MetricSnapshot.purchases).label("purchases_sum"),
            func.sum(MetricSnapshot.revenue).label("revenue_sum"),
        )
        .filter(MetricSnapshot.plan_id == plan_id)
        .filter(MetricSnapshot.date >= date_from)
        .filter(MetricSnapshot.date <= date_to)
    )

    result = query.first()

    # Если данных нет, возвращаем нули
    if result is None or all(v is None or v == 0 for v in [result.impressions_sum, result.clicks_sum, result.spend_sum]):
        impressions = 0
        clicks = 0
        spend = 0
        leads = 0
        purchases = 0
        revenue = 0
    else:
        impressions = result.impressions_sum or 0
        clicks = result.clicks_sum or 0
        spend = result.spend_sum or 0
        leads = result.leads_sum or 0
        purchases = result.purchases_sum or 0
        revenue = result.revenue_sum or 0

    # Вычисляем производные показатели (безопасное деление на ноль)
    cpc = (spend / clicks) if clicks > 0 else None
    cpl = (spend / leads) if leads > 0 else None
    cpa = (spend / purchases) if purchases > 0 else None

    return MetricsSummaryResponse(
        plan_id=plan_id,
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
        impressions=impressions,
        clicks=clicks,
        spend=spend,
        leads=leads,
        purchases=purchases,
        revenue=revenue,
        cpc=cpc,
        cpl=cpl,
        cpa=cpa,
    )
