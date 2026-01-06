from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, text, or_
from app.db.models import Connection, Experiment, ExperimentCampaign, MetricSnapshot, Platform, CampaignPlan
from app.services.connector_service import get_connector


def _metric_needs_update(stmt):
    return or_(
        MetricSnapshot.impressions.is_distinct_from(stmt.excluded.impressions),
        MetricSnapshot.clicks.is_distinct_from(stmt.excluded.clicks),
        MetricSnapshot.spend.is_distinct_from(stmt.excluded.spend),
        MetricSnapshot.leads.is_distinct_from(stmt.excluded.leads),
        MetricSnapshot.purchases.is_distinct_from(stmt.excluded.purchases),
        MetricSnapshot.revenue.is_distinct_from(stmt.excluded.revenue),
    )


def _apply_metric_upsert(db: Session, stmt, conflict_elements, conflict_where, set_values):
    insert_stmt = stmt.on_conflict_do_nothing(
        index_elements=conflict_elements,
        index_where=conflict_where,
    ).returning(MetricSnapshot.id)
    result = db.execute(insert_stmt)
    if result.first():
        return 1, 0, 0

    update_stmt = stmt.on_conflict_do_update(
        index_elements=conflict_elements,
        index_where=conflict_where,
        set_=set_values,
        where=_metric_needs_update(stmt),
    ).returning(MetricSnapshot.id)
    result = db.execute(update_stmt)
    if result.first():
        return 0, 1, 0
    return 0, 0, 1

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
    stats = {"inserted": 0, "updated": 0, "unchanged": 0, "total": len(raw_metrics)}

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

        inserted, updated, unchanged = _apply_metric_upsert(
            db,
            stmt,
            ["organization_id", "experiment_id", "platform", "date", "campaign_external_id"],
            text("level = 'campaign'"),
            {
                "impressions": stmt.excluded.impressions,
                "clicks": stmt.excluded.clicks,
                "spend": stmt.excluded.spend,
                "leads": stmt.excluded.leads,
                "purchases": stmt.excluded.purchases,
                "revenue": stmt.excluded.revenue,
                "updated_at": func.now(),
            },
        )
        stats["inserted"] += inserted
        stats["updated"] += updated
        stats["unchanged"] += unchanged

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
    records = connector.fetch_metrics(date_from, date_to)
    stats = {"inserted": 0, "updated": 0, "unchanged": 0, "total": len(records)}

    for record in records:
        record_date = record.get("date")
        if isinstance(record_date, str):
            record_date = date.fromisoformat(record_date)
        if record_date is None:
            raise ValueError("Metric record missing date")

        level = record.get("level") or "campaign"
        campaign_external_id = record.get("campaign_external_id")
        if not campaign_external_id:
            raise ValueError("Metric record missing campaign_external_id")

        ad_group_external_id = record.get("ad_group_external_id")
        ad_external_id = record.get("ad_external_id")

        if level == "ad_group" and not ad_group_external_id:
            raise ValueError("Metric record missing ad_group_external_id")
        if level == "ad" and (not ad_group_external_id or not ad_external_id):
            raise ValueError("Metric record missing ad_group_external_id or ad_external_id")

        stmt = insert(MetricSnapshot).values(
            organization_id=connection.organization_id,
            connection_id=connection.id,
            date=record_date,
            platform=connection.platform,
            level=level,
            campaign_external_id=str(campaign_external_id),
            ad_group_external_id=str(ad_group_external_id) if ad_group_external_id is not None else None,
            ad_external_id=str(ad_external_id) if ad_external_id is not None else None,
            impressions=int(record.get("impressions") or 0),
            clicks=int(record.get("clicks") or 0),
            spend=int(float(record.get("spend") or 0)),
            leads=int(float(record.get("leads") or 0)),
            purchases=int(float(record.get("purchases") or 0)),
            revenue=int(float(record.get("revenue") or 0)),
        )

        if level == "campaign":
            conflict_elements = ["organization_id", "connection_id", "platform", "date", "campaign_external_id"]
            conflict_where = text("level = 'campaign' AND connection_id IS NOT NULL")
        elif level == "ad_group":
            conflict_elements = [
                "organization_id",
                "connection_id",
                "platform",
                "date",
                "campaign_external_id",
                "ad_group_external_id",
            ]
            conflict_where = text("level = 'ad_group' AND connection_id IS NOT NULL")
        elif level == "ad":
            conflict_elements = [
                "organization_id",
                "connection_id",
                "platform",
                "date",
                "campaign_external_id",
                "ad_group_external_id",
                "ad_external_id",
            ]
            conflict_where = text("level = 'ad' AND connection_id IS NOT NULL")
        else:
            raise ValueError(f"Unsupported metric level: {level}")

        set_values = {
            "impressions": stmt.excluded.impressions,
            "clicks": stmt.excluded.clicks,
            "spend": stmt.excluded.spend,
            "leads": stmt.excluded.leads,
            "purchases": stmt.excluded.purchases,
            "revenue": stmt.excluded.revenue,
            "updated_at": func.now(),
        }

        if force:
            insert_stmt = stmt.on_conflict_do_nothing(
                index_elements=conflict_elements,
                index_where=conflict_where,
            )
            result = db.execute(insert_stmt)
            if result.rowcount:
                stats["inserted"] += 1
            else:
                update_stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_elements,
                    index_where=conflict_where,
                    set_=set_values,
                )
                result = db.execute(update_stmt)
                if result.rowcount:
                    stats["updated"] += 1
                else:
                    stats["unchanged"] += 1
        else:
            inserted, updated, unchanged = _apply_metric_upsert(
                db,
                stmt,
                conflict_elements,
                conflict_where,
                set_values,
            )
            stats["inserted"] += inserted
            stats["updated"] += updated
            stats["unchanged"] += unchanged

    db.commit()
    stats["date_from"] = date_from.isoformat()
    stats["date_to"] = date_to.isoformat()
    stats["platform"] = connection.platform.value
    return stats

# Legacy wrappers for backward compatibility if needed
def sync_yandex_campaigns(db: Session, experiment_id: int):
    return sync_campaigns(db, experiment_id, Platform.yandex)

def sync_yandex_metrics(db: Session, experiment_id: int, date_from: date, date_to: date):
    return sync_metrics(db, experiment_id, Platform.yandex, date_from, date_to)
