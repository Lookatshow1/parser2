from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.db.models import Connection, ConnectionStatus, SyncRun, SyncRunStatus
from app.api.schemas import (
    ConnectionCreateRequest,
    ConnectionOut,
    ConnectionListResponse,
    ConnectionTestResponse,
    ConnectionSyncRequest,
    ConnectionUpdateRequest,
    SyncRunListResponse,
    SyncRunResponse,
)
from app.api.deps import get_current_membership, get_current_org, get_current_user
from app.db.models import Organization, User
from app.services.connector_service import get_connector
from app.services.sync_run_service import create_connection_sync_run as create_sync_run
from app.services.rbac import can_run_sync, can_write_connections

router = APIRouter(prefix="/connections", tags=["connections"])

@router.post("", response_model=ConnectionOut)
def create_connection(
    item: ConnectionCreateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    if not can_write_connections(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role to create connection")
    db_obj = Connection(
        organization_id=org.id,
        advertiser_id=item.advertiser_id,
        platform=item.platform,
        name=item.name,
        credentials_json=item.credentials_json or {},
        auto_sync_enabled=item.auto_sync_enabled,
        auto_sync_every_minutes=item.auto_sync_every_minutes,
        auto_sync_window_days=item.auto_sync_window_days,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def _get_last_sync_by_connection(db: Session, connection_ids: list[int]) -> dict[int, SyncRun]:
    if not connection_ids:
        return {}
    runs = (
        db.query(SyncRun)
        .filter(SyncRun.connection_id.in_(connection_ids))
        .order_by(desc(SyncRun.created_at))
        .all()
    )
    last_by_conn: dict[int, SyncRun] = {}
    for run in runs:
        if run.connection_id and run.connection_id not in last_by_conn:
            last_by_conn[run.connection_id] = run
    return last_by_conn


@router.patch("/{connection_id}", response_model=ConnectionOut)
def update_connection(
    connection_id: int,
    payload: ConnectionUpdateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    if not can_write_connections(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role to update connection")
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    if payload.name is not None:
        conn.name = payload.name
    if payload.auto_sync_enabled is not None:
        conn.auto_sync_enabled = payload.auto_sync_enabled
    if payload.auto_sync_every_minutes is not None:
        conn.auto_sync_every_minutes = payload.auto_sync_every_minutes
    if payload.auto_sync_window_days is not None:
        conn.auto_sync_window_days = payload.auto_sync_window_days
    db.commit()
    db.refresh(conn)
    return conn

@router.get("", response_model=ConnectionListResponse)
def list_connections(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    items = db.query(Connection).filter(Connection.organization_id == org.id).all()
    last_by_conn = _get_last_sync_by_connection(db, [c.id for c in items])
    result_items = []
    for item in items:
        last = last_by_conn.get(item.id)
        payload = ConnectionOut.model_validate(item).model_dump()
        if last:
            payload["last_sync_status"] = last.status
            payload["last_sync_finished_at"] = last.finished_at
        result_items.append(payload)
    return {"items": result_items}

@router.get("/{connection_id}", response_model=ConnectionOut)
def get_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    last = (
        db.query(SyncRun)
        .filter(SyncRun.connection_id == conn.id)
        .order_by(desc(SyncRun.created_at))
        .first()
    )
    payload = ConnectionOut.model_validate(conn).model_dump()
    if last:
        payload["last_sync_status"] = last.status
        payload["last_sync_finished_at"] = last.finished_at
    return payload

@router.post("/{connection_id}/check", response_model=ConnectionTestResponse)
def check_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    if not can_write_connections(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role to check connection")
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    connector = get_connector(conn.platform, conn.credentials_json)
    try:
        result = connector.validate_connection(conn.credentials_json)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    ok = bool(result.get("ok"))
    message = result.get("message")
    error_code = result.get("error_code")
    if ok:
        conn.status = ConnectionStatus.active
    else:
        conn.status = ConnectionStatus.error
        conn.notes = message or conn.notes
    db.commit()
    return ConnectionTestResponse(ok=ok, message=message, error_code=error_code)

@router.post("/{connection_id}/sync", response_model=SyncRunResponse, status_code=status.HTTP_201_CREATED)
def create_connection_sync_run(
    connection_id: int,
    payload: ConnectionSyncRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    if not can_run_sync(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role to run sync")
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    active_run = (
        db.query(SyncRun)
        .filter(
            SyncRun.connection_id == conn.id,
            SyncRun.organization_id == org.id,
            SyncRun.status.in_([SyncRunStatus.queued, SyncRunStatus.running]),
        )
        .order_by(desc(SyncRun.created_at))
        .first()
    )
    if active_run:
        raise HTTPException(status_code=409, detail=f"Sync already running (run_id={active_run.id})")

    run = create_sync_run(
        db=db,
        connection=conn,
        date_from=payload.date_from,
        date_to=payload.date_to,
        force=payload.force,
    )
    return run

@router.get("/{connection_id}/sync-runs", response_model=SyncRunListResponse)
def list_connection_sync_runs(
    connection_id: int,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    query = db.query(SyncRun).filter(
        SyncRun.connection_id == connection_id,
        SyncRun.organization_id == org.id,
    )
    total = query.count()
    items = query.order_by(desc(SyncRun.created_at)).limit(limit).offset(offset).all()
    return {"items": items, "total": total}
