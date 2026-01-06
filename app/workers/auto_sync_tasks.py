from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db import session as db_session
from app.db.models import Connection, ConnectionStatus, SyncRun, SyncRunStatus
from app.services.lock_service import acquire_advisory_lock, get_auto_sync_lock_key
from app.services.sync_run_service import create_connection_sync_run
from app.workers.celery_app import celery_app


def _is_due(last_sync_at: datetime | None, every_minutes: int, now: datetime) -> bool:
    every_minutes = max(int(every_minutes or 1), 1)
    if last_sync_at is None:
        return True
    return now - last_sync_at >= timedelta(minutes=every_minutes)


def schedule_auto_syncs(db: Session, now: datetime | None = None, enqueue: bool = True) -> int:
    now = now or datetime.now(timezone.utc)
    total_scheduled = 0
    connections = (
        db.query(Connection)
        .filter(Connection.auto_sync_enabled.is_(True))
        .filter(Connection.status == ConnectionStatus.active)
        .all()
    )
    for conn in connections:
        if not _is_due(conn.last_auto_sync_at, conn.auto_sync_every_minutes, now):
            continue
        lock_key = get_auto_sync_lock_key(conn.id)
        if not acquire_advisory_lock(db, lock_key):
            continue

        active_run = (
            db.query(SyncRun)
            .filter(
                SyncRun.connection_id == conn.id,
                SyncRun.status.in_([SyncRunStatus.queued, SyncRunStatus.running]),
            )
            .first()
        )
        if active_run:
            continue

        date_to = now.date()
        date_from = date_to - timedelta(days=max(conn.auto_sync_window_days, 1) - 1)
        create_connection_sync_run(
            db=db,
            connection=conn,
            date_from=date_from,
            date_to=date_to,
            force=False,
            enqueue=enqueue,
        )
        conn.last_auto_sync_at = now
        db.commit()
        total_scheduled += 1

    return total_scheduled


@celery_app.task
def run_auto_sync_scheduler() -> int:
    db = db_session.get_session()
    try:
        return schedule_auto_syncs(db)
    finally:
        if not db_session.is_test_session(db):
            db.close()
