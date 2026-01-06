import os
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.schemas import ConnectionSyncRunCreateRequest, SyncRunResponse
from app.api.deps import get_current_org, get_current_user
from app.db.models import Connection, SyncRun, SyncRunStatus, SyncRunType, Organization, User
from app.db.session import get_db
from app.jobs.service import create_job
from app.workers.sync_tasks import execute_sync_run

router = APIRouter(prefix="/sync-runs", tags=["sync-runs"])

@router.post("", response_model=SyncRunResponse, status_code=status.HTTP_201_CREATED)
def create_sync_run(
    payload: ConnectionSyncRunCreateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    connection = db.query(Connection).filter(
        Connection.id == payload.connection_id,
        Connection.organization_id == org.id,
    ).first()
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

    if not os.getenv("PYTEST_CURRENT_TEST"):
        execute_sync_run.delay(run.id)
    return run


@router.get("/{run_id}", response_model=SyncRunResponse)
def get_sync_run(
    run_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    run = db.query(SyncRun).filter(SyncRun.id == run_id, SyncRun.organization_id == org.id).first()
    if not run:
        raise HTTPException(status_code=404, detail="SyncRun not found")
    return run


@router.get("", response_model=list[SyncRunResponse])
def list_sync_runs(
    connection_id: Optional[int] = Query(None, ge=1),
    status: Optional[SyncRunStatus] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    query = db.query(SyncRun)
    query = query.filter(SyncRun.organization_id == org.id)
    if connection_id:
        query = query.filter(SyncRun.connection_id == connection_id)
    if status:
        query = query.filter(SyncRun.status == status)
    return (
        query.order_by(desc(SyncRun.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
