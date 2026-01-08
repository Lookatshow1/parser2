from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas import MetricAggregateResponse, MetricTimeseriesResponse, MetricsSummaryResponse
from app.db.models import Connection, MetricSnapshot
from app.api.deps import get_current_org, get_current_user
from app.db.models import Organization, User
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
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    items = get_connection_metrics(
        session,
        connection_id=connection_id,
        organization_id=org.id,
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
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
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
        .filter(MetricSnapshot.organization_id == org.id)
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


@router.get("/timeseries", response_model=MetricTimeseriesResponse)
def metrics_timeseries(
    date_from: date | None = Query(None, description="Начало периода"),
    date_to: date | None = Query(None, description="Конец периода"),
    connection_ids: str | None = Query(None, description="Список connection_id через запятую"),
    metric_keys: str | None = Query(None, description="Список метрик через запятую"),
    granularity: str = Query("day", regex="^day$"),
    session: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    if date_to is None:
        date_to = datetime.utcnow().date()
    if date_from is None:
        date_from = date_to - timedelta(days=13)
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be <= date_to")
    if (date_to - date_from).days > 180:
        raise HTTPException(status_code=400, detail="date range exceeds 180 days")

    allowed_metrics = {
        "spend": MetricSnapshot.spend,
        "clicks": MetricSnapshot.clicks,
        "impressions": MetricSnapshot.impressions,
        "leads": MetricSnapshot.leads,
        "purchases": MetricSnapshot.purchases,
        "revenue": MetricSnapshot.revenue,
    }
    if metric_keys:
        requested = [item.strip() for item in metric_keys.split(",") if item.strip()]
    else:
        requested = ["spend", "clicks", "impressions"]
    invalid = [item for item in requested if item not in allowed_metrics]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unsupported metric_keys: {', '.join(invalid)}")

    conn_ids: list[int] = []
    if connection_ids:
        try:
            conn_ids = [int(item) for item in connection_ids.split(",") if item.strip()]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid connection_ids") from exc
        existing = session.execute(
            select(Connection.id).where(
                Connection.organization_id == org.id,
                Connection.id.in_(conn_ids),
            )
        ).scalars().all()
        if len(set(existing)) != len(set(conn_ids)):
            raise HTTPException(status_code=404, detail="Connection not found")
        conn_ids = list(set(existing))
    else:
        conn_ids = session.execute(
            select(Connection.id).where(Connection.organization_id == org.id)
        ).scalars().all()

    series: dict[str, list[dict]] = {key: [] for key in requested}
    totals: dict[str, int] = {key: 0 for key in requested}
    if not conn_ids:
        return {
            "date_from": date_from,
            "date_to": date_to,
            "series": series,
            "totals": totals,
        }

    for key in requested:
        col = allowed_metrics[key]
        query = (
            session.query(MetricSnapshot.date.label("date"), func.sum(col).label("value"))
            .filter(MetricSnapshot.organization_id == org.id)
            .filter(MetricSnapshot.connection_id.in_(conn_ids))
            .filter(MetricSnapshot.date >= date_from)
            .filter(MetricSnapshot.date <= date_to)
            .filter(MetricSnapshot.level == "campaign")
            .group_by(MetricSnapshot.date)
            .order_by(MetricSnapshot.date.asc())
        )
        rows = query.all()
        points = [{"date": row.date, "value": int(row.value or 0)} for row in rows]
        series[key] = points
        totals[key] = sum(point["value"] for point in points)

    return {
        "date_from": date_from,
        "date_to": date_to,
        "series": series,
        "totals": totals,
    }
