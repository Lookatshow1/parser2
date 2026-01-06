import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import ErirDevRegisterRequest, ErirDevRegisterResponse
from app.api.deps import get_current_membership, get_current_org, get_current_user
from app.db.models import ErirEvent, ErirStatus, Organization, User
from app.db.session import get_db
from app.jobs.service import create_job
from app.services.rbac import can_run_sync
from app.workers.erir_tasks import execute_erir_register

router = APIRouter(prefix="/erir", tags=["erir"])


@router.post("/dev/register", response_model=ErirDevRegisterResponse)
def erir_dev_register(
    payload: ErirDevRegisterRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    if not can_run_sync(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role for ERIR register")
    organization_id = org.id

    job = create_job(
        db,
        job_type="erir_register",
        context={
            "organization_id": organization_id,
            "connection_id": payload.connection_id,
        },
        organization_id=organization_id,
        connection_id=payload.connection_id,
    )

    event = ErirEvent(
        organization_id=organization_id,
        connection_id=payload.connection_id,
        event_type="register",
        status=ErirStatus.pending,
        payload_json=payload.payload_json,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    if not os.getenv("PYTEST_CURRENT_TEST"):
        execute_erir_register.delay(event.id, job.id)

    return ErirDevRegisterResponse(
        job_run_id=job.id,
        erir_event_id=event.id,
        status=event.status.value,
    )
