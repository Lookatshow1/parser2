from datetime import date
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import MetricSnapshot, Platform, ExperimentCampaign

def get_experiment_campaigns(
    db: Session,
    experiment_id: int,
    platform: Platform = Platform.yandex,
    limit: int = 100,
    offset: int = 0
):
    query = select(ExperimentCampaign).filter(
        ExperimentCampaign.experiment_id == experiment_id,
        ExperimentCampaign.platform == platform
    )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.execute(query.limit(limit).offset(offset)).scalars().all()
    return items, total

def get_experiment_metrics(
    db: Session,
    experiment_id: int,
    date_from: date,
    date_to: date,
    platform: Platform = Platform.yandex,
    group_by: str = "day",
    campaign_external_id: Optional[str] = None
):
    # Base query
    query = select(
        func.sum(MetricSnapshot.impressions).label("impressions"),
        func.sum(MetricSnapshot.clicks).label("clicks"),
        func.sum(MetricSnapshot.spend).label("spend"),
        func.sum(MetricSnapshot.leads).label("leads"),
        func.sum(MetricSnapshot.purchases).label("purchases"),
        func.sum(MetricSnapshot.revenue).label("revenue"),
    ).filter(
        MetricSnapshot.experiment_id == experiment_id,
        MetricSnapshot.platform == platform,
        MetricSnapshot.date >= date_from,
        MetricSnapshot.date <= date_to
    )

    if campaign_external_id:
        query = query.filter(MetricSnapshot.campaign_external_id == campaign_external_id)

    # Grouping
    if group_by == "day":
        query = query.add_columns(MetricSnapshot.date).group_by(MetricSnapshot.date).order_by(MetricSnapshot.date)
    elif group_by == "campaign":
        query = query.add_columns(MetricSnapshot.campaign_external_id).group_by(MetricSnapshot.campaign_external_id)
    elif group_by == "day_campaign":
        query = query.add_columns(MetricSnapshot.date, MetricSnapshot.campaign_external_id).group_by(MetricSnapshot.date, MetricSnapshot.campaign_external_id).order_by(MetricSnapshot.date)

    results = db.execute(query).all()

    # Transform and calculate derived metrics
    items = []
    for row in results:
        # row is a Row object, access by index or name
        # The order depends on add_columns

        # Base metrics are always first 6
        impressions = row.impressions or 0
        clicks = row.clicks or 0
        spend = row.spend or 0
        leads = row.leads or 0
        purchases = row.purchases or 0
        revenue = row.revenue or 0

        item = {
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "leads": leads,
            "purchases": purchases,
            "revenue": revenue,
            "ctr": (clicks / impressions * 100) if impressions > 0 else 0,
            "cpc": (spend / clicks) if clicks > 0 else 0,
            "cpm": (spend / impressions * 1000) if impressions > 0 else 0,
        }

        if group_by == "day":
            item["date"] = row.date
        elif group_by == "campaign":
            item["campaign_external_id"] = row.campaign_external_id
        elif group_by == "day_campaign":
            item["date"] = row.date
            item["campaign_external_id"] = row.campaign_external_id

        items.append(item)

    return items

def get_experiment_summary(
    db: Session,
    experiment_id: int,
    date_from: date,
    date_to: date,
    platform: Platform = Platform.yandex
):
    query = select(
        func.sum(MetricSnapshot.impressions).label("impressions"),
        func.sum(MetricSnapshot.clicks).label("clicks"),
        func.sum(MetricSnapshot.spend).label("spend"),
        func.sum(MetricSnapshot.leads).label("leads"),
        func.sum(MetricSnapshot.purchases).label("purchases"),
        func.sum(MetricSnapshot.revenue).label("revenue"),
    ).filter(
        MetricSnapshot.experiment_id == experiment_id,
        MetricSnapshot.platform == platform,
        MetricSnapshot.date >= date_from,
        MetricSnapshot.date <= date_to
    )

    row = db.execute(query).first()

    impressions = row.impressions or 0
    clicks = row.clicks or 0
    spend = row.spend or 0
    leads = row.leads or 0
    purchases = row.purchases or 0
    revenue = row.revenue or 0

    return {
        "impressions": impressions,
        "clicks": clicks,
        "spend": spend,
        "leads": leads,
        "purchases": purchases,
        "revenue": revenue,
        "ctr": (clicks / impressions * 100) if impressions > 0 else 0,
        "cpc": (spend / clicks) if clicks > 0 else 0,
        "cpm": (spend / impressions * 1000) if impressions > 0 else 0,
    }
