from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from app.db.models import Experiment, ExperimentCampaign, MetricSnapshot, Platform, CampaignPlan
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
        stmt = insert(MetricSnapshot).values(
            date=row["Date"],
            platform=platform,
            campaign_external_id=str(row["CampaignId"]),
            experiment_id=experiment_id,
            plan_id=experiment.plan_id,
            connection_id=experiment.plan.connection_id,
            impressions=row["Impressions"],
            clicks=row["Clicks"],
            spend=row["Cost"]
        )

        stmt = stmt.on_conflict_do_update(
            constraint='uq_metric_snapshot',
            set_={
                "impressions": stmt.excluded.impressions,
                "clicks": stmt.excluded.clicks,
                "spend": stmt.excluded.spend,
                "updated_at": func.now() # Assuming updated_at exists or just to trigger update
            }
        )
        result = db.execute(stmt)

    db.commit()
    return stats

# Legacy wrappers for backward compatibility if needed
def sync_yandex_campaigns(db: Session, experiment_id: int):
    return sync_campaigns(db, experiment_id, Platform.yandex)

def sync_yandex_metrics(db: Session, experiment_id: int, date_from: date, date_to: date):
    return sync_metrics(db, experiment_id, Platform.yandex, date_from, date_to)
