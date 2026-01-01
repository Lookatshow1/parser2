from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import ComplianceRegisterRequest, ComplianceRegisterResponse
from app.db.session import get_db
from app.services.compliance_registry import ComplianceRegistry

router = APIRouter(prefix="/compliance")


@router.post("/register", response_model=ComplianceRegisterResponse)
def register_compliance(
    payload: ComplianceRegisterRequest,
    session: Session = Depends(get_db),
):
    registry = ComplianceRegistry()
    try:
        registry.register(session, payload.creative_variant_id, payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ComplianceRegisterResponse(ok=True)
