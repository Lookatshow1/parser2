from fastapi import APIRouter

from app.api.schemas import ConnectionTestRequest, ConnectionTestResponse
from app.services.connector_service import ConnectorService

router = APIRouter(prefix="/connections")


@router.post("/test", response_model=ConnectionTestResponse)
def test_connection(payload: ConnectionTestRequest):
    connector_service = ConnectorService()
    connector = connector_service.get(payload.platform)
    ok = connector.validate_connection(payload.credentials_json)
    return ConnectionTestResponse(ok=ok)
