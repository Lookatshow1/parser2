"""
Сервис для KPI дашборда с нормализацией метрик
"""
from datetime import date, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.db.models import MetricSnapshot, Connection, Platform


def build_kpi_timeseries(
    db: Session,
    org_id: int,
    date_from: date,
    date_to: date,
    connection_ids: Optional[list[int]] = None,
    platform: Optional[str] = None,
    mode: str = "index"
) -> dict:
    """
    Построить таймсерию KPI с нормализацией.
    
    Args:
        db: Database session
        org_id: Organization ID
        date_from: Start date
        date_to: End date
        connection_ids: Optional list of connection IDs (org scoped)
        platform: Optional platform filter (yandex/vk/ozon)
        mode: "index" or "absolute"
    
    Returns:
        dict with items (timeseries) and meta
    """
    # 1. Validate connection_ids (org scoping)
    if connection_ids:
        valid_conn_ids_list = db.execute(
            select(Connection.id)
            .where(Connection.organization_id == org_id)
            .where(Connection.id.in_(connection_ids))
        ).scalars().all()
        
        valid_conn_ids = list(valid_conn_ids_list)
        
        if len(valid_conn_ids) != len(connection_ids):
            # Not all connections belong to org - raise 404 for security
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404,
                detail="Одно или несколько подключений не найдено или не принадлежит организации"
            )
    else:
        # Get all connections for org
        valid_conn_ids = db.execute(
            select(Connection.id)
            .where(Connection.organization_id == org_id)
        ).scalars().all()
    
    if not valid_conn_ids:
        return {
            "items": [],
            "meta": {
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "mode": mode,
                "platform": platform,
                "connection_ids": connection_ids or []
            }
        }
    
    # 2. Build query
    query = (
        select(
            MetricSnapshot.date,
            func.sum(MetricSnapshot.impressions).label("impressions"),
            func.sum(MetricSnapshot.clicks).label("clicks"),
            func.sum(MetricSnapshot.purchases).label("conversions"),  # purchases as conversions
            func.sum(MetricSnapshot.spend).label("spend"),
        )
        .where(MetricSnapshot.organization_id == org_id)
        .where(MetricSnapshot.connection_id.in_(valid_conn_ids))
        .where(MetricSnapshot.date >= date_from)
        .where(MetricSnapshot.date <= date_to)
        .where(MetricSnapshot.level == "campaign")  # Use campaign level to avoid double counting
    )
    
    # Filter by platform if specified
    if platform:
        try:
            platform_enum = Platform(platform)
            query = query.where(MetricSnapshot.platform == platform_enum)
        except ValueError:
            pass  # Invalid platform, ignore filter
    
    query = query.group_by(MetricSnapshot.date).order_by(MetricSnapshot.date)
    
    # 3. Execute query
    rows = db.execute(query).all()
    
    # 4. Process data
    items = []
    raw_data = []
    
    for row in rows:
        d = {
            "date": row.date.isoformat(),
            "impressions": int(row.impressions or 0),
            "clicks": int(row.clicks or 0),
            "conversions": int(row.conversions or 0),
            "spend": int(row.spend or 0),
        }
        raw_data.append(d)
    
    if not raw_data:
        return {
            "items": [],
            "meta": {
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "mode": mode,
                "platform": platform,
                "connection_ids": connection_ids or []
            }
        }
    
    # 5. Calculate max values for normalization
    max_impressions = max(d["impressions"] for d in raw_data) if raw_data else 0
    max_clicks = max(d["clicks"] for d in raw_data) if raw_data else 0
    max_conversions = max(d["conversions"] for d in raw_data) if raw_data else 0
    max_spend = max(d["spend"] for d in raw_data) if raw_data else 0
    
    # 6. Build items with normalization
    for d in raw_data:
        item = {
            "date": d["date"],
            "impressions": d["impressions"],
            "clicks": d["clicks"],
            "conversions": d["conversions"],
            "spend": d["spend"],
        }
        
        if mode == "index":
            # Normalize to 0-100
            item["impressions_index"] = round((d["impressions"] / max_impressions * 100) if max_impressions > 0 else 0.0, 1)
            item["clicks_index"] = round((d["clicks"] / max_clicks * 100) if max_clicks > 0 else 0.0, 1)
            item["conversions_index"] = round((d["conversions"] / max_conversions * 100) if max_conversions > 0 else 0.0, 1)
            item["spend_index"] = round((d["spend"] / max_spend * 100) if max_spend > 0 else 0.0, 1)
        else:
            # Absolute mode - no indices
            item["impressions_index"] = None
            item["clicks_index"] = None
            item["conversions_index"] = None
            item["spend_index"] = None
        
        items.append(item)
    
    return {
        "items": items,
        "meta": {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "mode": mode,
            "platform": platform,
            "connection_ids": connection_ids or []
        }
    }


def build_kpi_summary(
    db: Session,
    org_id: int,
    date_from: date,
    date_to: date,
    connection_ids: Optional[list[int]] = None,
    platform: Optional[str] = None
) -> dict:
    """
    Построить сводку KPI для карточек.
    
    Args:
        db: Database session
        org_id: Organization ID
        date_from: Start date
        date_to: End date
        connection_ids: Optional list of connection IDs (org scoped)
        platform: Optional platform filter (yandex/vk/ozon)
    
    Returns:
        dict with KPI metrics
    """
    # 1. Validate connection_ids (org scoping)
    if connection_ids:
        valid_conn_ids_list = db.execute(
            select(Connection.id)
            .where(Connection.organization_id == org_id)
            .where(Connection.id.in_(connection_ids))
        ).scalars().all()
        
        valid_conn_ids = list(valid_conn_ids_list)
        
        if len(valid_conn_ids) != len(connection_ids):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404,
                detail="Одно или несколько подключений не найдено или не принадлежит организации"
            )
    else:
        valid_conn_ids_list = db.execute(
            select(Connection.id)
            .where(Connection.organization_id == org_id)
        ).scalars().all()
        valid_conn_ids = list(valid_conn_ids_list)
    
    if not valid_conn_ids:
        return {
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "spend": 0,
            "ctr": None,
            "cpc": None,
            "cpa": None,
            "currency": "RUB"
        }
    
    # 2. Build query
    query = (
        select(
            func.sum(MetricSnapshot.impressions).label("impressions"),
            func.sum(MetricSnapshot.clicks).label("clicks"),
            func.sum(MetricSnapshot.purchases).label("conversions"),
            func.sum(MetricSnapshot.spend).label("spend"),
        )
        .where(MetricSnapshot.organization_id == org_id)
        .where(MetricSnapshot.connection_id.in_(valid_conn_ids))
        .where(MetricSnapshot.date >= date_from)
        .where(MetricSnapshot.date <= date_to)
        .where(MetricSnapshot.level == "campaign")
    )
    
    # Filter by platform if specified
    if platform:
        try:
            platform_enum = Platform(platform)
            query = query.where(MetricSnapshot.platform == platform_enum)
        except ValueError:
            pass
    
    # 3. Execute query
    row = db.execute(query).first()
    
    impressions = int(row.impressions or 0)
    clicks = int(row.clicks or 0)
    conversions = int(row.conversions or 0)
    spend = int(row.spend or 0)
    
    # 4. Calculate derived metrics
    ctr = round((clicks / impressions * 100), 2) if impressions > 0 else None
    cpc = round((spend / clicks), 2) if clicks > 0 else None
    cpa = round((spend / conversions), 2) if conversions > 0 else None
    
    return {
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "spend": spend,
        "ctr": ctr,
        "cpc": cpc,
        "cpa": cpa,
        "currency": "RUB"
    }
