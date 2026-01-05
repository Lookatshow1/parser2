import traceback
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import SyncRun, SyncRunStatus, SyncRunType
from app.jobs.service import mark_failed, mark_running, mark_succeeded
from app.services.lock_service import acquire_advisory_lock, get_sync_lock_key, get_connection_sync_lock_key
from app.services.sync_service import sync_campaigns, sync_metrics, sync_connection_metrics

def _run_sync_logic(db: Session, run: SyncRun):
    """
    Executes the actual sync logic based on run_type.
    """
    params = run.params_json

    if run.connection_id:
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        if not date_from or not date_to:
            from datetime import date, timedelta
            d_to = date.today()
            d_from = d_to - timedelta(days=2)
        else:
            from datetime import date
            d_from = date.fromisoformat(str(date_from))
            d_to = date.fromisoformat(str(date_to))
        force = bool(params.get("force", False))
        return sync_connection_metrics(db, run.connection_id, d_from, d_to, force=force)

    experiment_id = run.experiment_id
    platform = run.platform

    if run.run_type == SyncRunType.campaigns:
        return sync_campaigns(db, experiment_id, platform)

    elif run.run_type == SyncRunType.metrics:
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        if not date_from or not date_to:
            raise ValueError("date_from and date_to are required for metrics sync")

        from datetime import date
        d_from = date.fromisoformat(str(date_from))
        d_to = date.fromisoformat(str(date_to))
        return sync_metrics(db, experiment_id, platform, d_from, d_to)

    elif run.run_type == SyncRunType.full:
        # First campaigns
        result_campaigns = sync_campaigns(db, experiment_id, platform)

        # Then metrics
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        if date_from and date_to:
            from datetime import date
            d_from = date.fromisoformat(str(date_from))
            d_to = date.fromisoformat(str(date_to))
            result_metrics = sync_metrics(db, experiment_id, platform, d_from, d_to)
            return {"campaigns": result_campaigns, "metrics": result_metrics}
        return {"campaigns": result_campaigns}

@shared_task(bind=True, max_retries=3)
def execute_sync_run(self, run_id: int):
    db = SessionLocal()
    try:
        run = db.query(SyncRun).get(run_id)
        if not run:
            return "SyncRun not found"

        job_run_id = None
        if run.params_json:
            job_run_id = run.params_json.get("job_run_id")

        # 1. Try to acquire lock
        if run.connection_id:
            lock_key = get_connection_sync_lock_key(run.connection_id, run.platform)
        else:
            lock_key = get_sync_lock_key(run.experiment_id, run.platform)
        if not acquire_advisory_lock(db, lock_key):
            run.status = SyncRunStatus.failed
            run.error_text = "Already running (lock acquisition failed)"
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            if job_run_id:
                mark_failed(db, job_run_id, "Already running (lock acquisition failed)")
            return "Lock failed"

        # 2. Mark running
        run.status = SyncRunStatus.running
        run.started_at = datetime.now(timezone.utc)
        db.commit()
        if job_run_id:
            mark_running(db, job_run_id)

        # 3. Execute logic
        try:
            result = _run_sync_logic(db, run)

            run.status = SyncRunStatus.success
            run.finished_at = datetime.now(timezone.utc)
            run.result_json = result or {}
            db.commit()
            if job_run_id:
                mark_succeeded(db, job_run_id, {"result": result or {}})

        except Exception as e:
            db.rollback()
            # Refresh run to update status
            run = db.query(SyncRun).get(run_id)
            run.status = SyncRunStatus.failed
            error_text = f"{str(e)}\n{traceback.format_exc()}"
            run.error_text = error_text[:4000]
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            if job_run_id:
                mark_failed(db, job_run_id, str(e))

            # Retry logic for network errors could be here
            # self.retry(exc=e, countdown=60)

    finally:
        db.close()
