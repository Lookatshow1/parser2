import traceback
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db import session as db_session
from app.db.models import SyncRun, SyncRunStatus, SyncRunType
from app.jobs.service import mark_failed, mark_running, mark_succeeded
from app.services.lock_service import acquire_advisory_lock, get_sync_lock_key, get_connection_sync_lock_key
from app.services.audit import log_org_event
from app.services.sync_service import sync_campaigns, sync_metrics, sync_connection_metrics
from app.workers.celery_app import celery_app
from app.core.context import set_correlation_id

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
            d_from = d_to - timedelta(days=13)
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

@celery_app.task(bind=True, max_retries=3)
def execute_sync_run(self, run_id: int, correlation_id: str | None = None):
    # Set correlation ID for logging
    if correlation_id:
        set_correlation_id(correlation_id)

    db = db_session.get_session()
    lock_key = None
    try:
        run = db.query(SyncRun).get(run_id)
        if not run:
            return "SyncRun not found"

        job_run_id = None
        if run.params_json:
            job_run_id = run.params_json.get("job_run_id")

        # 1. Try to acquire lock
        if run.connection_id:
            lock_key = get_connection_sync_lock_key(run.connection_id, run.platform, run.organization_id)
        else:
            lock_key = get_sync_lock_key(run.experiment_id, run.platform)
        if not acquire_advisory_lock(db, lock_key):
            run.status = SyncRunStatus.failed
            run.error_text = "Already running (lock acquisition failed)"
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
            if run.connection_id:
                log_org_event(
                    db,
                    organization_id=run.organization_id,
                    actor_user_id=None,
                    action="connection_sync_failed",
                    subject_type="connection",
                    subject_id=run.connection_id,
                    meta={"reason": "lock_failed", "sync_run_id": run.id},
                )
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
            duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
            if isinstance(result, dict):
                result = {**result, "duration_ms": duration_ms}
            else:
                result = {"result": result, "duration_ms": duration_ms}
            run.result_json = result or {}
            db.commit()
            if run.connection_id:
                log_org_event(
                    db,
                    organization_id=run.organization_id,
                    actor_user_id=None,
                    action="connection_sync_succeeded",
                    subject_type="connection",
                    subject_id=run.connection_id,
                    meta={
                        "sync_run_id": run.id,
                        "inserted": result.get("inserted") if isinstance(result, dict) else None,
                        "updated": result.get("updated") if isinstance(result, dict) else None,
                        "unchanged": result.get("unchanged") if isinstance(result, dict) else None,
                    },
                )
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
            if run.connection_id:
                log_org_event(
                    db,
                    organization_id=run.organization_id,
                    actor_user_id=None,
                    action="connection_sync_failed",
                    subject_type="connection",
                    subject_id=run.connection_id,
                    meta={"sync_run_id": run.id, "error": str(e)[:500]},
                )
            if job_run_id:
                mark_failed(db, job_run_id, str(e))

            # Retry logic for network errors could be here
            # self.retry(exc=e, countdown=60)

    finally:
        if lock_key is not None:
            db.info.get("advisory_locks", set()).discard(lock_key)
        if not db_session.is_test_session(db):
            db.close()
