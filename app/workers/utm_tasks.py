from __future__ import annotations

from app.db.session import SessionLocal
from app.db.models import Connection
from app.services.utm_reconcile_service import reconcile_ads_utm_for_connection
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.utm_tasks.run_utm_reconcile_scheduler")
def run_utm_reconcile_scheduler() -> dict:
    db = SessionLocal()
    try:
        connections = db.query(Connection).all()
        total = 0
        for conn in connections:
            reconcile_ads_utm_for_connection(db, conn)
            total += 1
        return {"processed": total}
    finally:
        db.close()
