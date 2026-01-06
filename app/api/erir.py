from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import ErirDevRegisterRequest, ErirDevRegisterResponse
from app.core.config import get_settings
from app.db.models import ErirEvent, ErirStatus
from app.db.session import get_db
from app.jobs.service import create_job
from app.workers.erir_tasks import execute_erir_register

router = APIRouter(prefix="/erir", tags=["erir"])


@router.post("/dev/register", response_model=ErirDevRegisterResponse)
def erir_dev_register(payload: ErirDevRegisterRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    organization_id = payload.organization_id or settings.default_organization_id

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

    execute_erir_register.delay(event.id, job.id)

    return ErirDevRegisterResponse(
        job_run_id=job.id,
        erir_event_id=event.id,
        status=event.status.value,
    )
