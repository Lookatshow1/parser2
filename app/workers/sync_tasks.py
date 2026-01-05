import traceback
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import SyncRun, SyncRunStatus, SyncRunType
from app.services.lock_service import acquire_advisory_lock, get_sync_lock_key
from app.services.sync_service import sync_yandex_campaigns, sync_yandex_metrics

def _run_sync_logic(db: Session, run: SyncRun):
    """
    Executes the actual sync logic based on run_type.
    """
    experiment_id = run.experiment_id
    platform = run.platform
    params = run.params_json

    if run.run_type == SyncRunType.campaigns:
        if platform == "yandex":
            sync_yandex_campaigns(db, experiment_id)

    elif run.run_type == SyncRunType.metrics:
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        if not date_from or not date_to:
            raise ValueError("date_from and date_to are required for metrics sync")

        if platform == "yandex":
            # Convert strings to date objects if needed, sync_yandex_metrics expects dates or strings?
            # Looking at sync_service.py, it expects date objects or strings that can be parsed.
            # Let's pass as is, assuming service handles it or they are strings.
            # Actually sync_yandex_metrics type hint says date, so let's parse.
            from datetime import date
            d_from = date.fromisoformat(str(date_from))
            d_to = date.fromisoformat(str(date_to))
            sync_yandex_metrics(db, experiment_id, d_from, d_to)

    elif run.run_type == SyncRunType.full:
        # First campaigns
        if platform == "yandex":
            sync_yandex_campaigns(db, experiment_id)

        # Then metrics
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        if date_from and date_to:
            if platform == "yandex":
                from datetime import date
                d_from = date.fromisoformat(str(date_from))
                d_to = date.fromisoformat(str(date_to))
                sync_yandex_metrics(db, experiment_id, d_from, d_to)

@shared_task(bind=True, max_retries=3)
def execute_sync_run(self, run_id: int):
    db = SessionLocal()
    try:
        run = db.query(SyncRun).get(run_id)
        if not run:
            return "SyncRun not found"

        # 1. Try to acquire lock
        lock_key = get_sync_lock_key(run.experiment_id, run.platform)
        if not acquire_advisory_lock(db, lock_key):
            run.status = SyncRunStatus.failed
            run.error_text = "Already running (lock acquisition failed)"
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            return "Lock failed"

        # 2. Mark running
        run.status = SyncRunStatus.running
        run.started_at = datetime.now(timezone.utc)
        db.commit()

        # 3. Execute logic
        try:
            _run_sync_logic(db, run)

            run.status = SyncRunStatus.success
            run.finished_at = datetime.now(timezone.utc)
            db.commit()

        except Exception as e:
            db.rollback()
            # Refresh run to update status
            run = db.query(SyncRun).get(run_id)
            run.status = SyncRunStatus.failed
            run.error_text = f"{str(e)}\n{traceback.format_exc()}"
            run.finished_at = datetime.now(timezone.utc)
            db.commit()

            # Retry logic for network errors could be here
            # self.retry(exc=e, countdown=60)

    finally:
        db.close()
