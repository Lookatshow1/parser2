import os
from datetime import date, timedelta
from typing import Tuple

from sqlalchemy.orm import Session

from app.db.models import Connection, SyncRun, SyncRunStatus, SyncRunType
from app.jobs.service import create_job
from app.workers.sync_tasks import execute_sync_run


def build_date_range(
    date_from: date | None,
    date_to: date | None,
    window_days: int = 14,
) -> Tuple[date, date]:
    if date_from and date_to:
        return date_from, date_to
    date_to = date.today()
    date_from = date_to - timedelta(days=max(window_days, 1) - 1)
    return date_from, date_to


def create_connection_sync_run(
    db: Session,
    connection: Connection,
    date_from: date | None,
    date_to: date | None,
    force: bool = False,
    enqueue: bool = True,
) -> SyncRun:
    d_from, d_to = build_date_range(date_from, date_to, window_days=connection.auto_sync_window_days or 14)
    context = {
        "connection_id": connection.id,
        "date_from": d_from.isoformat(),
        "date_to": d_to.isoformat(),
        "force": force,
    }
    job = create_job(
        db,
        job_type="connection_sync",
        context=context,
        organization_id=connection.organization_id,
        connection_id=connection.id,
    )

    params = dict(context)
    params["job_run_id"] = job.id

    run = SyncRun(
        organization_id=connection.organization_id,
        connection_id=connection.id,
        platform=connection.platform,
        run_type=SyncRunType.metrics,
        status=SyncRunStatus.queued,
        params_json=params,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if enqueue and not os.getenv("PYTEST_CURRENT_TEST"):
        execute_sync_run.delay(run.id)
    return run
