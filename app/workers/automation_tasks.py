from __future__ import annotations

from datetime import datetime

from app.db.session import SessionLocal
from app.db.models import Organization
from app.services.automation_service import run_automation_for_org, should_run, get_or_create_settings
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.automation_tasks.run_automation_for_org")
def run_automation_for_org_task(org_id: int) -> dict:
    db = SessionLocal()
    try:
        org = db.query(Organization).get(org_id)
        if not org:
            return {"status": "org_not_found"}
        run = run_automation_for_org(db, org, actor_user_id=None)
        return {"status": run.status, "run_id": run.id}
    finally:
        db.close()


@celery_app.task(name="app.workers.automation_tasks.run_automation_scheduler")
def run_automation_scheduler() -> dict:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        org_ids = [row[0] for row in db.query(Organization.id).all()]
        scheduled = 0
        for org_id in org_ids:
            settings = get_or_create_settings(db, org_id)
            if not should_run(settings, now):
                continue
            run_automation_for_org_task.delay(settings.organization_id)
            settings.last_run_at = now
            scheduled += 1
        db.commit()
        return {"scheduled": scheduled}
    finally:
        db.close()
