from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, text
from app.db.models import Connection, Experiment, ExperimentCampaign, MetricSnapshot, Platform, CampaignPlan
from app.services.connector_service import get_connector

def sync_campaigns(db: Session, experiment_id: int, platform: Platform):
    # 1. Get Experiment and Connection
    experiment = db.query(Experiment).join(Experiment.plan).filter(Experiment.id == experiment_id).first()
    if not experiment or not experiment.plan.connection:
        raise ValueError("Experiment or Connection not found")

    if experiment.plan.connection.platform != platform:
         raise ValueError(f"Connection platform {experiment.plan.connection.platform} does not match requested {platform}")

    connector = get_connector(platform, experiment.plan.connection.credentials_json)

    # 2. Fetch from API
    campaigns = connector.list_campaigns()

    # 3. Upsert to DB
    stats = {"created": 0, "updated": 0, "total": len(campaigns)}

    for camp in campaigns:
        stmt = insert(ExperimentCampaign).values(
            organization_id=experiment.organization_id,
            experiment_id=experiment_id,
            platform=platform,
            campaign_external_id=str(camp["id"])
        )
        # Do nothing on conflict
        stmt = stmt.on_conflict_do_nothing(
            index_elements=['experiment_id', 'platform', 'campaign_external_id']
        )
        result = db.execute(stmt)
        if result.rowcount > 0:
            stats["created"] += 1
        else:
            stats["updated"] += 1

    db.commit()
    return stats

def sync_metrics(db: Session, experiment_id: int, platform: Platform, date_from: date, date_to: date):
    # 1. Get Context
    experiment = db.query(Experiment).join(Experiment.plan).filter(Experiment.id == experiment_id).first()
    if not experiment or not experiment.plan.connection:
        raise ValueError("Experiment or Connection not found")

    if experiment.plan.connection.platform != platform:
         raise ValueError(f"Connection platform {experiment.plan.connection.platform} does not match requested {platform}")

    # 2. Get Linked Campaigns
    linked_campaigns = db.query(ExperimentCampaign.campaign_external_id)\
        .filter(ExperimentCampaign.experiment_id == experiment_id, ExperimentCampaign.platform == platform)\
        .all()
    campaign_ids = [r[0] for r in linked_campaigns]

    if not campaign_ids:
        return {"status": "no_campaigns"}

    # 3. Fetch Metrics
    connector = get_connector(platform, experiment.plan.connection.credentials_json)
    raw_metrics = connector.get_daily_stats(campaign_ids, date_from, date_to)

    # 4. Upsert Metrics
    stats = {"created": 0, "updated": 0, "total": len(raw_metrics)}

    for row in raw_metrics:
        date_value = date.fromisoformat(str(row["Date"]))
        stmt = insert(MetricSnapshot).values(
            date=date_value,
            platform=platform,
            level="campaign",
            campaign_external_id=str(row["CampaignId"]),
            organization_id=experiment.organization_id,
            experiment_id=experiment_id,
            plan_id=experiment.plan_id,
            connection_id=experiment.plan.connection_id,
            impressions=row["Impressions"],
            clicks=row["Clicks"],
            spend=int(float(row["Cost"] or 0)),
            leads=int(float(row.get("Leads") or 0)),
            purchases=int(float(row.get("Purchases") or 0)),
            revenue=int(float(row.get("Revenue") or 0)),
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["organization_id", "experiment_id", "platform", "date", "campaign_external_id"],
            index_where=text("level = 'campaign'"),
            set_={
                "impressions": stmt.excluded.impressions,
                "clicks": stmt.excluded.clicks,
                "spend": stmt.excluded.spend,
                "leads": stmt.excluded.leads,
                "purchases": stmt.excluded.purchases,
                "revenue": stmt.excluded.revenue,
            },
        )
        result = db.execute(stmt)
        if result.rowcount:
            stats["created"] += 1
        else:
            stats["updated"] += 1

    db.commit()
    return stats


def sync_connection_metrics(
    db: Session,
    connection_id: int,
    date_from: date,
    date_to: date,
    force: bool = False,
):
    connection = db.query(Connection).get(connection_id)
    if not connection:
        raise ValueError("Connection not found")

    connector = get_connector(connection.platform, connection.credentials_json)
    campaigns = connector.list_campaigns()
    campaign_ids = [str(camp["id"]) for camp in campaigns]

    if not campaign_ids:
        return {"status": "no_campaigns", "total": 0}

    raw_metrics = connector.get_daily_stats(campaign_ids, date_from, date_to)
    stats = {"created": 0, "updated": 0, "total": len(raw_metrics)}

    for row in raw_metrics:
        date_value = date.fromisoformat(str(row["Date"]))
        stmt = insert(MetricSnapshot).values(
            organization_id=connection.organization_id,
            connection_id=connection.id,
            date=date_value,
            platform=connection.platform,
            level="campaign",
            campaign_external_id=str(row["CampaignId"]),
            impressions=int(row.get("Impressions") or 0),
            clicks=int(row.get("Clicks") or 0),
            spend=int(float(row.get("Cost") or 0)),
            leads=int(float(row.get("Leads") or 0)),
            purchases=int(float(row.get("Purchases") or 0)),
            revenue=int(float(row.get("Revenue") or 0)),
        )

        if force:
            stmt = stmt.on_conflict_do_update(
                index_elements=["organization_id", "connection_id", "platform", "date", "campaign_external_id"],
                index_where=text("level = 'campaign' AND connection_id IS NOT NULL"),
                set_={
                    "impressions": stmt.excluded.impressions,
                    "clicks": stmt.excluded.clicks,
                    "spend": stmt.excluded.spend,
                    "leads": stmt.excluded.leads,
                    "purchases": stmt.excluded.purchases,
                    "revenue": stmt.excluded.revenue,
                },
            )
        else:
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["organization_id", "connection_id", "platform", "date", "campaign_external_id"],
                index_where=text("level = 'campaign' AND connection_id IS NOT NULL"),
            )

        result = db.execute(stmt)
        if result.rowcount:
            stats["created"] += 1
        else:
            stats["updated"] += 1

    db.commit()
    return stats

# Legacy wrappers for backward compatibility if needed
def sync_yandex_campaigns(db: Session, experiment_id: int):
    return sync_campaigns(db, experiment_id, Platform.yandex)

def sync_yandex_metrics(db: Session, experiment_id: int, date_from: date, date_to: date):
    return sync_metrics(db, experiment_id, Platform.yandex, date_from, date_to)
