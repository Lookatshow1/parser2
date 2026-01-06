from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import ConnectionSyncRunCreateRequest, SyncRunResponse
from app.db.models import Connection, SyncRun, SyncRunStatus, SyncRunType
from app.db.session import get_db
from app.jobs.service import create_job
from app.workers.sync_tasks import execute_sync_run

router = APIRouter(prefix="/sync-runs", tags=["sync-runs"])

@router.post("", response_model=SyncRunResponse, status_code=status.HTTP_201_CREATED)
def create_sync_run(payload: ConnectionSyncRunCreateRequest, db: Session = Depends(get_db)):
    connection = db.query(Connection).get(payload.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    params = dict(payload.params_json or {})
    if "date_from" not in params or "date_to" not in params:
        date_to = date.today()
        date_from = date_to - timedelta(days=2)
        params.setdefault("date_from", date_from.isoformat())
        params.setdefault("date_to", date_to.isoformat())

    job = create_job(
        db,
        job_type="connection_sync",
        context={"connection_id": connection.id, **params},
        organization_id=connection.organization_id,
        connection_id=connection.id,
    )
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

    execute_sync_run.delay(run.id)
    return run


@router.get("/{run_id}", response_model=SyncRunResponse)
def get_sync_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(SyncRun).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="SyncRun not found")
    return run
