from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.schemas import ConnectionSyncRunCreateRequest, SyncRunResponse
from app.api.deps import get_current_membership, get_current_org, get_current_user
from app.db.models import Connection, SyncRun, SyncRunStatus, Organization, User
from app.db.session import get_db
from app.services.rbac import can_run_sync
from app.services.sync_run_service import create_connection_sync_run

router = APIRouter(prefix="/sync-runs", tags=["sync-runs"])

@router.post("", response_model=SyncRunResponse, status_code=status.HTTP_201_CREATED)
def create_sync_run(
    payload: ConnectionSyncRunCreateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    if not can_run_sync(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role to run sync")
    connection = db.query(Connection).filter(
        Connection.id == payload.connection_id,
        Connection.organization_id == org.id,
    ).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    active_run = (
        db.query(SyncRun)
        .filter(
            SyncRun.connection_id == connection.id,
            SyncRun.organization_id == org.id,
            SyncRun.status.in_([SyncRunStatus.queued, SyncRunStatus.running]),
        )
        .order_by(desc(SyncRun.created_at))
        .first()
    )
    if active_run:
        raise HTTPException(status_code=409, detail=f"Sync already running (run_id={active_run.id})")

    params = dict(payload.params_json or {})
    if "date_from" not in params or "date_to" not in params:
        date_to = date.today()
        date_from = date_to - timedelta(days=2)
        params.setdefault("date_from", date_from.isoformat())
        params.setdefault("date_to", date_to.isoformat())
    return create_connection_sync_run(
        db=db,
        connection=connection,
        date_from=date.fromisoformat(str(params["date_from"])),
        date_to=date.fromisoformat(str(params["date_to"])),
        force=bool(params.get("force", False)),
    )


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
    limit: int = Query(20, ge=1, le=200),
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
