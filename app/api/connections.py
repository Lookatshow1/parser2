import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.db.models import Connection, ConnectionStatus, SyncRun, SyncRunStatus, SyncRunType
from app.api.schemas import (
    ConnectionCreateRequest,
    ConnectionOut,
    ConnectionListResponse,
    ConnectionTestResponse,
    ConnectionSyncRequest,
    SyncRunListResponse,
    SyncRunResponse,
)
from app.api.deps import get_current_org, get_current_user
from app.db.models import Organization, User
from app.jobs.service import create_job
from app.services.connector_service import get_connector
from app.workers.sync_tasks import execute_sync_run

router = APIRouter(prefix="/connections", tags=["connections"])

@router.post("", response_model=ConnectionOut)
def create_connection(
    item: ConnectionCreateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    db_obj = Connection(
        organization_id=org.id,
        advertiser_id=item.advertiser_id,
        platform=item.platform,
        name=item.name,
        credentials_json=item.credentials_json
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("", response_model=ConnectionListResponse)
def list_connections(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    items = db.query(Connection).filter(Connection.organization_id == org.id).all()
    return {"items": items}

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
    return conn

@router.post("/{connection_id}/check", response_model=ConnectionTestResponse)
def check_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
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
):
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    context = {
        "connection_id": conn.id,
        "date_from": payload.date_from.isoformat(),
        "date_to": payload.date_to.isoformat(),
        "force": payload.force,
    }
    job = create_job(
        db,
        job_type="connection_sync",
        context=context,
        organization_id=conn.organization_id,
        connection_id=conn.id,
    )

    params = dict(context)
    params["job_run_id"] = job.id

    run = SyncRun(
        organization_id=conn.organization_id,
        connection_id=conn.id,
        platform=conn.platform,
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

@router.get("/{connection_id}/sync-runs", response_model=SyncRunListResponse)
def list_connection_sync_runs(
    connection_id: int,
    limit: int = Query(50, ge=1, le=200),
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
