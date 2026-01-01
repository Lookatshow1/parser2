from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.schemas import (
    ConnectionCreateRequest,
    ConnectionListResponse,
    ConnectionResponse,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from app.db.models import Connection
from app.db.session import get_db
from fastapi import HTTPException
from app.services.connector_service import ConnectorService

router = APIRouter(prefix="/connections")


@router.get("", response_model=ConnectionListResponse)
def list_connections(session: Session = Depends(get_db)):
    connections = session.scalars(select(Connection)).all()
    return ConnectionListResponse(
        items=[
            ConnectionResponse(
                id=item.id,
                advertiser_id=item.advertiser_id,
                platform=item.platform,
                status=item.status.value,
            )
            for item in connections
        ]
    )


@router.post("", response_model=ConnectionResponse)
def create_connection(payload: ConnectionCreateRequest, session: Session = Depends(get_db)):
    connection = Connection(
        advertiser_id=payload.advertiser_id,
        platform=payload.platform,
        credentials_json=payload.credentials_json,
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)
    return ConnectionResponse(
        id=connection.id,
        advertiser_id=connection.advertiser_id,
        platform=connection.platform,
        status=connection.status.value,
    )


@router.post("/test", response_model=ConnectionTestResponse, deprecated=True)
def test_connection(payload: ConnectionTestRequest):
    connector_service = ConnectorService()
    connector = connector_service.get(payload.platform)
    ok = connector.validate_connection(payload.credentials_json)
    return ConnectionTestResponse(ok=ok)


@router.post("/{connection_id}/test", response_model=ConnectionTestResponse)
def test_connection_by_id(connection_id: int, session: Session = Depends(get_db)):
    connection = session.scalar(select(Connection).where(Connection.id == connection_id))
    if connection is None:
        raise HTTPException(status_code=404, detail="Connection not found")
    connector_service = ConnectorService()
    connector = connector_service.get(connection.platform)
    ok = connector.validate_connection(connection.credentials_json)
    return ConnectionTestResponse(ok=ok)
