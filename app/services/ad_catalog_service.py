from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, select, distinct
from app.db.models import Connection, MetricSnapshot, AdCampaign, AdAdGroup, AdAd, Platform

def refresh_catalog_for_connection(db: Session, connection_id: int):
    """
    Refreshes ad catalog (campaigns, groups, ads) from metric snapshots for a given connection.
    Idempotent: inserts missing entities, updates existing ones (though names are static for now).
    """
    connection = db.query(Connection).get(connection_id)
    if not connection:
        return {"status": "connection_not_found"}

    # 1. Campaigns
    # Select distinct campaign_external_id from snapshots
    campaigns_query = (
        select(
            distinct(MetricSnapshot.campaign_external_id)
        )
        .where(MetricSnapshot.connection_id == connection_id)
        .where(MetricSnapshot.campaign_external_id.isnot(None))
    )
    campaign_ids = db.execute(campaigns_query).scalars().all()

    campaign_stats = {"created": 0, "updated": 0}
    for cid in campaign_ids:
        stmt = insert(AdCampaign).values(
            organization_id=connection.organization_id,
            connection_id=connection_id,
            platform=connection.platform,
            external_id=cid,
            name=f"Кампания {cid}", # Placeholder name
            updated_at=func.now()
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["connection_id", "external_id"],
            set_={"updated_at": func.now()}
        )
        result = db.execute(stmt)
        if result.rowcount > 0: # rowcount is driver dependent, but usually works for upsert
             # For on_conflict_do_update, rowcount might be 1 (insert) or 1 (update) or 2 (update) depending on driver
             # We just track that we processed it.
             pass

    # 2. Ad Groups
    groups_query = (
        select(
            distinct(MetricSnapshot.ad_group_external_id),
            MetricSnapshot.campaign_external_id
        )
        .where(MetricSnapshot.connection_id == connection_id)
        .where(MetricSnapshot.ad_group_external_id.isnot(None))
    )
    groups = db.execute(groups_query).all()

    for gid, cid in groups:
        stmt = insert(AdAdGroup).values(
            organization_id=connection.organization_id,
            connection_id=connection_id,
            platform=connection.platform,
            external_id=gid,
            campaign_external_id=cid,
            name=f"Группа {gid}",
            updated_at=func.now()
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["connection_id", "external_id"],
            set_={"updated_at": func.now(), "campaign_external_id": cid}
        )
        db.execute(stmt)

    # 3. Ads
    ads_query = (
        select(
            distinct(MetricSnapshot.ad_external_id),
            MetricSnapshot.ad_group_external_id,
            MetricSnapshot.campaign_external_id
        )
        .where(MetricSnapshot.connection_id == connection_id)
        .where(MetricSnapshot.ad_external_id.isnot(None))
    )
    ads = db.execute(ads_query).all()

    for aid, gid, cid in ads:
        stmt = insert(AdAd).values(
            organization_id=connection.organization_id,
            connection_id=connection_id,
            platform=connection.platform,
            external_id=aid,
            ad_group_external_id=gid,
            campaign_external_id=cid,
            name=f"Объявление {aid}",
            updated_at=func.now()
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["connection_id", "external_id"],
            set_={"updated_at": func.now(), "ad_group_external_id": gid, "campaign_external_id": cid}
        )
        db.execute(stmt)

    db.commit()
    return {"campaigns": len(campaign_ids), "groups": len(groups), "ads": len(ads)}
