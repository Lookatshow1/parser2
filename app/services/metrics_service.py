from datetime import date
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import MetricSnapshot, Platform, ExperimentCampaign, Experiment

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
    # Get experiment to check plan_id
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        return []
    
    # Check if experiment has campaigns defined
    experiment_campaigns = db.query(ExperimentCampaign).filter(
        ExperimentCampaign.experiment_id == experiment_id,
        ExperimentCampaign.platform == platform
    ).all()
    
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
        MetricSnapshot.date <= date_to,
        MetricSnapshot.level == "campaign",
    )
    
    # If experiment has campaigns defined, filter by them and plan_id
    if experiment_campaigns and experiment.plan_id:
        campaign_ids = [c.campaign_external_id for c in experiment_campaigns]
        query = query.filter(
            MetricSnapshot.plan_id == experiment.plan_id,
            MetricSnapshot.campaign_external_id.in_(campaign_ids)
        )
    elif experiment.plan_id:
        # Fallback: filter by plan_id only
        query = query.filter(MetricSnapshot.plan_id == experiment.plan_id)

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


def get_experiment_report_metrics(
    db: Session,
    experiment_id: int,
    date_from: date | None = None,
    date_to: date | None = None
):
    """
    Get metrics for experiment report, grouped by date and platform.
    Returns list of dicts with date, platform, impressions, clicks, spend.
    """
    # Get experiment to check plan_id and platforms
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        return []
    
    # Get all platforms for this experiment
    platforms = [Platform(p) for p in (experiment.platforms or [])]
    if not platforms:
        platforms = [Platform.yandex]  # default
    
    # Default date range: last 30 days if not specified
    if date_from is None or date_to is None:
        from datetime import datetime, timedelta
        date_to = datetime.utcnow().date()
        date_from = date_to - timedelta(days=30)
    
    # Check if experiment has campaigns defined
    experiment_campaigns_all = db.query(ExperimentCampaign).filter(
        ExperimentCampaign.experiment_id == experiment_id
    ).all()
    
    campaign_map: dict[str, list[str]] = {}
    for c in experiment_campaigns_all:
        campaign_map.setdefault(c.platform.value, []).append(c.campaign_external_id)
    
    metrics = []
    for platform in platforms:
        # Build query for this platform
        query = select(
            MetricSnapshot.date,
            func.sum(MetricSnapshot.impressions).label("impressions"),
            func.sum(MetricSnapshot.clicks).label("clicks"),
            func.sum(MetricSnapshot.spend).label("spend"),
        ).filter(
            MetricSnapshot.experiment_id == experiment_id,
            MetricSnapshot.platform == platform,
            MetricSnapshot.date >= date_from,
            MetricSnapshot.date <= date_to,
            MetricSnapshot.level == "campaign",
        )
        
        # If experiment has campaigns defined for this platform, filter by them and plan_id
        if campaign_map.get(platform.value) and experiment.plan_id:
            campaign_ids = campaign_map[platform.value]
            query = query.filter(
                MetricSnapshot.plan_id == experiment.plan_id,
                MetricSnapshot.campaign_external_id.in_(campaign_ids)
            )
        elif experiment.plan_id:
            # Fallback: filter by plan_id only
            query = query.filter(MetricSnapshot.plan_id == experiment.plan_id)
        
        query = query.group_by(MetricSnapshot.date).order_by(MetricSnapshot.date)
        
        results = db.execute(query).all()
        for row in results:
            metrics.append({
                "date": row.date.isoformat() if row.date else None,
                "platform": platform.value,
                "impressions": row.impressions or 0,
                "clicks": row.clicks or 0,
                "spend": row.spend or 0,
            })
    
    return metrics


def get_experiment_summary(
    db: Session,
    experiment_id: int,
    date_from: date,
    date_to: date,
    platform: Platform = Platform.yandex
):
    # Get experiment to check plan_id
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        return {
            "impressions": 0,
            "clicks": 0,
            "spend": 0,
            "leads": 0,
            "purchases": 0,
            "revenue": 0,
            "ctr": 0,
            "cpc": 0,
            "cpm": 0,
        }
    
    # Check if experiment has campaigns defined
    experiment_campaigns = db.query(ExperimentCampaign).filter(
        ExperimentCampaign.experiment_id == experiment_id,
        ExperimentCampaign.platform == platform
    ).all()
    
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
        MetricSnapshot.date <= date_to,
        MetricSnapshot.level == "campaign",
    )
    
    # If experiment has campaigns defined, filter by them and plan_id
    if experiment_campaigns and experiment.plan_id:
        campaign_ids = [c.campaign_external_id for c in experiment_campaigns]
        query = query.filter(
            MetricSnapshot.plan_id == experiment.plan_id,
            MetricSnapshot.campaign_external_id.in_(campaign_ids)
        )
    elif experiment.plan_id:
        # Fallback: filter by plan_id only
        query = query.filter(MetricSnapshot.plan_id == experiment.plan_id)

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


def get_connection_metrics(
    db: Session,
    connection_id: int,
    organization_id: int,
    date_from: date,
    date_to: date,
    group_by: str = "day",
    campaign_external_id: Optional[str] = None,
):
    query = select(
        func.sum(MetricSnapshot.impressions).label("impressions"),
        func.sum(MetricSnapshot.clicks).label("clicks"),
        func.sum(MetricSnapshot.spend).label("spend"),
        func.sum(MetricSnapshot.leads).label("leads"),
        func.sum(MetricSnapshot.purchases).label("purchases"),
        func.sum(MetricSnapshot.revenue).label("revenue"),
    ).filter(
        MetricSnapshot.connection_id == connection_id,
        MetricSnapshot.organization_id == organization_id,
        MetricSnapshot.date >= date_from,
        MetricSnapshot.date <= date_to,
        MetricSnapshot.level == "campaign",
    )

    if campaign_external_id:
        query = query.filter(MetricSnapshot.campaign_external_id == campaign_external_id)

    if group_by == "day":
        query = query.add_columns(MetricSnapshot.date).group_by(MetricSnapshot.date).order_by(MetricSnapshot.date)
    elif group_by == "campaign":
        query = query.add_columns(MetricSnapshot.campaign_external_id).group_by(MetricSnapshot.campaign_external_id)
    elif group_by == "day_campaign":
        query = query.add_columns(MetricSnapshot.date, MetricSnapshot.campaign_external_id).group_by(
            MetricSnapshot.date, MetricSnapshot.campaign_external_id
        ).order_by(MetricSnapshot.date)

    results = db.execute(query).all()
    items = []
    for row in results:
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
