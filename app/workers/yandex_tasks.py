import logging
from datetime import date, datetime

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text

from app.connectors.yandex_direct import YandexDirectConnector
from app.db.models import Connection, MetricSnapshot
from app.db.session import SessionLocal
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def sync_yandex_metrics(self, connection_id: int, plan_id: int, date_from: str, date_to: str) -> dict:
    logger.info(
        f"Starting sync_yandex_metrics: connection_id={connection_id}, "
        f"plan_id={plan_id}, date_from={date_from}, date_to={date_to}"
    )
    
    session: Session = SessionLocal()
    try:
        connection = session.get(Connection, connection_id)
        if not connection:
            error_msg = f"Connection not found: connection_id={connection_id}"
            logger.error(error_msg)
            return {
                "saved": 0,
                "error": "Connection not found",
                "connection_id": connection_id,
            }

        connector = YandexDirectConnector(connection.credentials_json)
        metrics = connector.fetch_metrics(date.fromisoformat(date_from), date.fromisoformat(date_to))
        
        logger.info(f"Fetched {len(metrics)} metrics from Yandex API")

        rows = []
        now = datetime.utcnow()
        for m in metrics:
            rows.append(
                {
                    "organization_id": connection.organization_id,
                    "date": m["date"],
                    "platform": m["platform"],
                    "level": m.get("level") or "campaign",
                    "campaign_external_id": m["campaign_external_id"],
                    "clicks": m["clicks"],
                    "impressions": m["impressions"],
                    "spend": m["spend"],
                    "leads": m["leads"],
                    "purchases": m["purchases"],
                    "revenue": m["revenue"],
                    "plan_id": plan_id,
                    "connection_id": connection_id,
                    "created_at": now,
                }
            )

        saved_count = 0
        if rows:
            stmt = insert(MetricSnapshot).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["organization_id", "connection_id", "platform", "date", "campaign_external_id"],
                index_where=text("level = 'campaign' AND connection_id IS NOT NULL"),
                set_={
                    "clicks": stmt.excluded.clicks,
                    "impressions": stmt.excluded.impressions,
                    "spend": stmt.excluded.spend,
                    "leads": stmt.excluded.leads,
                    "purchases": stmt.excluded.purchases,
                    "revenue": stmt.excluded.revenue,
                },
            )
            result = session.execute(stmt)
            saved_count = result.rowcount if result.rowcount is not None else len(rows)

        session.commit()
        logger.info(
            f"Sync completed: fetched={len(metrics)}, saved={saved_count}, "
            f"connection_id={connection_id}, plan_id={plan_id}"
        )
        return {"saved": saved_count}
    except Exception as exc:
        logger.error(
            f"Error in sync_yandex_metrics: connection_id={connection_id}, "
            f"plan_id={plan_id}, error={str(exc)}",
            exc_info=True,
        )
        session.rollback()
        raise
    finally:
        session.close()
