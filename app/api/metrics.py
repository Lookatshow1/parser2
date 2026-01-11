from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, desc, asc
from sqlalchemy.orm import Session

from app.api.schemas import (
    MetricAggregateResponse,
    MetricTimeseriesResponse,
    MetricsSummaryResponse,
    MetricsBreakdownResponse,
    MetricsBreakdownItem
)
from app.db.models import Connection, MetricSnapshot, AdCampaign, AdAdGroup, AdAd, Platform
from app.api.deps import get_current_org, get_current_user
from app.db.models import Organization, User
from app.db.session import get_db
from app.services.metrics_service import get_connection_metrics

router = APIRouter(prefix="/metrics")


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
    connection_ids: list[str] | None = Query(None, description="Список connection_id"),
    metric_keys: str | None = Query(None, description="Список метрик через запятую"),
    granularity: str = Query("day", regex="^day$"),
    campaign_external_id: str | None = Query(None),
    ad_group_external_id: str | None = Query(None),
    ad_external_id: str | None = Query(None),
    session: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    if date_to is None:
        date_to = datetime.utcnow().date()
    if date_from is None:
        date_from = date_to - timedelta(days=13)
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="Дата начала не может быть позже даты окончания")
    if (date_to - date_from).days > 366:
        raise HTTPException(status_code=400, detail="Диапазон дат не должен превышать 366 дней")

    if metric_keys:
        allowed_metrics = {"spend", "clicks", "impressions", "leads", "purchases", "revenue"}
        requested = [item.strip() for item in metric_keys.split(",") if item.strip()]
        invalid = [item for item in requested if item not in allowed_metrics]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Недопустимые метрики: {', '.join(invalid)}")

    conn_ids: list[int] = []
    if connection_ids:
        raw_ids: list[str] = []
        for item in connection_ids:
            raw_ids.extend([part.strip() for part in item.split(",") if part.strip()])
        try:
            conn_ids = [int(item) for item in raw_ids]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Некорректный список подключений") from exc
        existing = session.execute(
            select(Connection.id).where(
                Connection.organization_id == org.id,
                Connection.id.in_(conn_ids),
            )
        ).scalars().all()
        if len(set(existing)) != len(set(conn_ids)):
            raise HTTPException(status_code=404, detail="Подключение не найдено")
        conn_ids = list(set(existing))
    else:
        conn_ids = session.execute(
            select(Connection.id).where(Connection.organization_id == org.id)
        ).scalars().all()

    if not conn_ids:
        empty_totals = _calc_efficiency(0, 0, 0, 0, 0)
        return {
            "date_from": date_from,
            "date_to": date_to,
            "items": [],
            "totals": {
                "impressions": 0,
                "clicks": 0,
                "spend": 0,
                "leads": 0,
                "purchases": 0,
                "revenue": 0,
                **empty_totals,
            },
        }

    query = (
        session.query(
            MetricSnapshot.date,
            func.coalesce(func.sum(MetricSnapshot.impressions), 0),
            func.coalesce(func.sum(MetricSnapshot.clicks), 0),
            func.coalesce(func.sum(MetricSnapshot.spend), 0),
            func.coalesce(func.sum(MetricSnapshot.leads), 0),
            func.coalesce(func.sum(MetricSnapshot.purchases), 0),
            func.coalesce(func.sum(MetricSnapshot.revenue), 0),
        )
        .filter(MetricSnapshot.organization_id == org.id)
        .filter(MetricSnapshot.connection_id.in_(conn_ids))
        .filter(MetricSnapshot.date >= date_from)
        .filter(MetricSnapshot.date <= date_to)
    )

    # Filter logic
    if ad_external_id:
        query = query.filter(MetricSnapshot.ad_external_id == ad_external_id)
        # Usually level='ad' contains ad_external_id, but sometimes we aggregate up.
        # If we filter by ad_external_id, we should look at level='ad' rows to be precise,
        # or rely on the fact that ad_external_id is populated.
        # MetricSnapshot stores data at specific levels.
        # If we want timeseries for an ad, we should filter level='ad'.
        query = query.filter(MetricSnapshot.level == 'ad')
    elif ad_group_external_id:
        query = query.filter(MetricSnapshot.ad_group_external_id == ad_group_external_id)
        # Aggregating ad_group level rows OR ad level rows?
        # Ideally we have rows for 'ad_group' level.
        # If not, we sum 'ad' rows.
        # Let's assume we have 'ad_group' level rows or we sum 'ad' rows.
        # Safer to filter by level if we have it.
        # But if we just filter by ID, we might double count if we have both 'ad' and 'ad_group' rows for same events.
        # MetricSnapshot structure: one row per entity per date per level.
        # So for a group, we should look at level='ad_group' OR sum(level='ad').
        # Let's stick to level='ad_group' if available, or just filter by ID and level IN ...
        # Simplest: filter by ID and level='ad_group' (assuming sync creates it).
        # If sync doesn't create ad_group level snapshots, we must sum ads.
        # Current sync implementation creates snapshots at the level returned by API.
        # Yandex sync usually returns campaign stats.
        # If we want drilldown, we need deeper sync.
        # For now, let's assume we filter by what's available.
        # To avoid double counting, we should pick one level.
        query = query.filter(MetricSnapshot.level == 'ad_group')
    elif campaign_external_id:
        query = query.filter(MetricSnapshot.campaign_external_id == campaign_external_id)
        query = query.filter(MetricSnapshot.level == 'campaign')
    else:
        # Default: sum campaigns
        query = query.filter(MetricSnapshot.level == 'campaign')

    rows = query.group_by(MetricSnapshot.date).order_by(MetricSnapshot.date.asc()).all()

    items = []
    totals_row = {"impressions": 0, "clicks": 0, "spend": 0, "leads": 0, "purchases": 0, "revenue": 0}
    for row in rows:
        impressions = int(row[1])
        clicks = int(row[2])
        spend = int(row[3])
        leads = int(row[4])
        purchases = int(row[5])
        revenue = int(row[6])
        totals_row["impressions"] += impressions
        totals_row["clicks"] += clicks
        totals_row["spend"] += spend
        totals_row["leads"] += leads
        totals_row["purchases"] += purchases
        totals_row["revenue"] += revenue
        items.append(
            {
                "date": row[0],
                "impressions": impressions,
                "clicks": clicks,
                "spend": spend,
                "leads": leads,
                "purchases": purchases,
                "revenue": revenue,
                **_calc_efficiency(impressions, clicks, spend, purchases, revenue),
            }
        )

    totals = {
        **totals_row,
        **_calc_efficiency(
            totals_row["impressions"],
            totals_row["clicks"],
            totals_row["spend"],
            totals_row["purchases"],
            totals_row["revenue"],
        ),
    }

    return {
        "date_from": date_from,
        "date_to": date_to,
        "items": items,
        "totals": totals,
    }

@router.get("/breakdown", response_model=MetricsBreakdownResponse)
def metrics_breakdown(
    date_from: date = Query(..., description="Начало периода"),
    date_to: date = Query(..., description="Конец периода"),
    dimension: str = Query(..., regex="^(campaign|ad_group|ad)$"),
    connection_ids: list[str] | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    query: str | None = Query(None),
    order_by: str = Query("spend", regex="^(spend|clicks|impressions|ctr|cpc|cpm|cpa|roas)$"),
    session: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    # 1. Resolve connections
    conn_ids: list[int] = []
    if connection_ids:
        raw_ids: list[str] = []
        for item in connection_ids:
            raw_ids.extend([part.strip() for part in item.split(",") if part.strip()])
        try:
            conn_ids = [int(item) for item in raw_ids]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Некорректный список подключений") from exc
        existing = session.execute(
            select(Connection.id).where(
                Connection.organization_id == org.id,
                Connection.id.in_(conn_ids),
            )
        ).scalars().all()
        if len(set(existing)) != len(set(conn_ids)):
            raise HTTPException(status_code=404, detail="Подключение не найдено")
        conn_ids = list(set(existing))
    else:
        conn_ids = session.execute(
            select(Connection.id).where(Connection.organization_id == org.id)
        ).scalars().all()

    if not conn_ids:
        return {"items": [], "total": 0}

    # 2. Build Query
    # We aggregate MetricSnapshot by external_id
    # And join with Catalog tables to get names

    # Select fields
    sel = [
        MetricSnapshot.platform,
        func.sum(MetricSnapshot.spend).label("spend"),
        func.sum(MetricSnapshot.impressions).label("impressions"),
        func.sum(MetricSnapshot.clicks).label("clicks"),
        func.sum(MetricSnapshot.leads).label("leads"),
        func.sum(MetricSnapshot.purchases).label("purchases"),
        func.sum(MetricSnapshot.revenue).label("revenue"),
    ]

    group_by_cols = [MetricSnapshot.platform]

    if dimension == "campaign":
        sel.append(MetricSnapshot.campaign_external_id.label("external_id"))
        # Join AdCampaign to get name and internal id
        # We need to join on (connection_id, external_id)
        # But MetricSnapshot has connection_id too.
        # Since we aggregate, we group by external_id.
        # Note: external_id is unique per connection, but might collide across connections?
        # Usually external_id is unique globally or per platform.
        # Safer to group by (connection_id, external_id) if we want to distinguish same ID in diff connections.
        # But here we want to show list of campaigns.
        # Let's group by external_id AND connection_id to be safe, or just external_id if we assume uniqueness.
        # Catalog tables have unique(connection_id, external_id).
        # So we should group by connection_id too?
        # If we group by connection_id, we split same campaign if it moved connections (unlikely).
        # Let's group by campaign_external_id and pick any connection_id (or max) to join?
        # Or better: group by campaign_external_id.
        # And we need name.
        # We can subquery or join.
        # Simple approach: Group by campaign_external_id. Name can be fetched via join if we assume 1-to-1 mapping.
        # If multiple connections have same campaign_id (e.g. re-added), we merge them?
        # Let's assume we merge them.
        group_by_cols.append(MetricSnapshot.campaign_external_id)

        # To get name, we can use a subquery or join.
        # Since we group by external_id, we need an aggregate for name or join.
        # Let's try to join AdCampaign.
        # But AdCampaign is per connection.
        # If we have multiple connections, we might have multiple AdCampaign rows for same external_id.
        # Let's just pick max(name).

    elif dimension == "ad_group":
        sel.append(MetricSnapshot.ad_group_external_id.label("external_id"))
        group_by_cols.append(MetricSnapshot.ad_group_external_id)
    elif dimension == "ad":
        sel.append(MetricSnapshot.ad_external_id.label("external_id"))
        group_by_cols.append(MetricSnapshot.ad_external_id)

    q = (
        session.query(*sel)
        .filter(MetricSnapshot.organization_id == org.id)
        .filter(MetricSnapshot.connection_id.in_(conn_ids))
        .filter(MetricSnapshot.date >= date_from)
        .filter(MetricSnapshot.date <= date_to)
        .filter(MetricSnapshot.level == dimension) # Important: filter by level to avoid double counting
    )

    if query:
        # Search by external_id or name.
        # Searching by name requires join or subquery.
        # For MVP, let's search by external_id in snapshot,
        # OR we can filter having name ILIKE ... (requires join).
        # Let's implement search by external_id first.
        if dimension == "campaign":
            q = q.filter(MetricSnapshot.campaign_external_id.ilike(f"%{query}%"))
        elif dimension == "ad_group":
            q = q.filter(MetricSnapshot.ad_group_external_id.ilike(f"%{query}%"))
        elif dimension == "ad":
            q = q.filter(MetricSnapshot.ad_external_id.ilike(f"%{query}%"))

    q = q.group_by(*group_by_cols)

    # Total count (approximate or separate query)
    # SQLAlchemy count on grouped query is tricky.
    # We can fetch all and slice in python (if not too many), or use subquery.
    # Given limit 500, fetching all might be heavy if thousands.
    # Let's use subquery for count.
    sub = q.subquery()
    total = session.query(func.count()).select_from(sub).scalar()

    # Sorting
    # We can sort in DB by aggregated fields.
    # KPI sorting (ctr/cpc) requires expression.
    # spend, clicks, impressions are direct.

    sort_map = {
        "spend": desc("spend"),
        "clicks": desc("clicks"),
        "impressions": desc("impressions"),
        # Derived
        "ctr": desc(text("clicks::float / nullif(impressions, 0)")),
        "cpc": asc(text("spend::float / nullif(clicks, 0)")), # Lower CPC is better? Usually sorting by cost desc means most expensive.
        # Let's stick to desc for "big numbers" and user expectation.
        # If user wants cheapest CPC, they might expect asc.
        # But standard grids usually sort desc by default.
        # Let's use desc for everything for simplicity, or handle specific logic.
        # API spec says "order_by", default spend desc.
        # Let's implement desc for all for now.
    }

    if order_by in ["cpc", "cpa", "cpm"]:
        # Cost metrics: usually we want to see highest cost first? Or lowest?
        # Let's use desc (highest first) as default behavior for "top lists".
        pass

    # Apply sort
    if order_by == "ctr":
        q = q.order_by(desc(text("sum(clicks)::float / nullif(sum(impressions), 0)")))
    elif order_by == "cpc":
        q = q.order_by(desc(text("sum(spend)::float / nullif(sum(clicks), 0)")))
    elif order_by == "cpm":
        q = q.order_by(desc(text("sum(spend)::float * 1000 / nullif(sum(impressions), 0)")))
    elif order_by == "cpa":
        q = q.order_by(desc(text("sum(spend)::float / nullif(sum(purchases), 0)")))
    elif order_by == "roas":
        q = q.order_by(desc(text("sum(revenue)::float / nullif(sum(spend), 0)")))
    else:
        q = q.order_by(desc(text(f"sum({order_by})")))

    # Pagination
    rows = q.limit(limit).offset(offset).all()

    # Post-processing: fetch names
    # Collect external_ids
    ext_ids = [r.external_id for r in rows]
    names_map = {}

    if ext_ids:
        if dimension == "campaign":
            # Fetch names from AdCampaign
            # We pick any name for this external_id (limit 1)
            # In case of multiple connections, names should be identical or we pick one.
            camps = session.query(AdCampaign.external_id, AdCampaign.name, AdCampaign.id).filter(
                AdCampaign.external_id.in_(ext_ids),
                AdCampaign.connection_id.in_(conn_ids)
            ).all()
            for eid, name, iid in camps:
                names_map[eid] = (name, iid)
        elif dimension == "ad_group":
            groups = session.query(AdAdGroup.external_id, AdAdGroup.name, AdAdGroup.id).filter(
                AdAdGroup.external_id.in_(ext_ids),
                AdAdGroup.connection_id.in_(conn_ids)
            ).all()
            for eid, name, iid in groups:
                names_map[eid] = (name, iid)
        elif dimension == "ad":
            ads = session.query(AdAd.external_id, AdAd.name, AdAd.id).filter(
                AdAd.external_id.in_(ext_ids),
                AdAd.connection_id.in_(conn_ids)
            ).all()
            for eid, name, iid in ads:
                names_map[eid] = (name, iid)

    items = []
    for row in rows:
        # row keys: platform, spend, impressions, clicks, leads, purchases, revenue, external_id
        # SQLAlchemy row is tuple-like or keyed.
        # Let's access by index or name.
        # Index: 0=platform, 1=spend, 2=impressions, 3=clicks, 4=leads, 5=purchases, 6=revenue, 7=external_id

        spend = int(row[1] or 0)
        impressions = int(row[2] or 0)
        clicks = int(row[3] or 0)
        leads = int(row[4] or 0)
        purchases = int(row[5] or 0)
        revenue = int(row[6] or 0)
        ext_id = row[7]

        name_info = names_map.get(ext_id, (None, None))
        name = name_info[0] or f"#{ext_id}"
        internal_id = name_info[1]

        eff = _calc_efficiency(impressions, clicks, spend, purchases, revenue)

        items.append(MetricsBreakdownItem(
            dimension=dimension,
            id=internal_id,
            external_id=ext_id,
            name=name,
            platform=row[0],
            spend=spend,
            impressions=impressions,
            clicks=clicks,
            leads=leads,
            purchases=purchases,
            revenue=revenue,
            **eff
        ))

    return {"items": items, "total": total}
