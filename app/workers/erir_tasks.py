import traceback
from datetime import datetime, timezone

from app.db import session as db_session
from app.db.models import ErirEvent, ErirStatus
from app.jobs.service import mark_failed, mark_running, mark_succeeded
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=1)
def execute_erir_register(self, erir_event_id: int, job_run_id: int):
    db = db_session.get_session()
    try:
        event = db.query(ErirEvent).get(erir_event_id)
        if not event:
            mark_failed(db, job_run_id, "ERIR event not found")
            return "ERIR event not found"

        event.status = ErirStatus.running
        event.updated_at = datetime.now(timezone.utc)
        db.commit()
        mark_running(db, job_run_id)

        try:
            result = {
                "provider": "dev_stub",
                "received_at": datetime.now(timezone.utc).isoformat(),
            }
            event.status = ErirStatus.success
            event.result_json = result
            event.updated_at = datetime.now(timezone.utc)
            db.commit()
            mark_succeeded(db, job_run_id, result)
            return result
        except Exception as exc:
            db.rollback()
            event = db.query(ErirEvent).get(erir_event_id)
            event.status = ErirStatus.failed
            event.error_text = str(exc)
            event.updated_at = datetime.now(timezone.utc)
            db.commit()
            mark_failed(db, job_run_id, str(exc))
            return "failed"
    except Exception as exc:
        db.rollback()
        error_text = f"{exc}\n{traceback.format_exc()}"
        mark_failed(db, job_run_id, error_text[:4000])
        return "failed"
    finally:
        if not db_session.is_test_session(db):
            db.close()
