from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    ExperimentCloseResponse,
    ExperimentCreateRequest,
    ExperimentReportResponse,
    ExperimentResponse,
)
from app.db.session import get_db
from app.services.experiment_service import ExperimentService
from app.workers.experiment_tasks import close_round_task

router = APIRouter(prefix="/experiments")


@router.post("/create", response_model=ExperimentResponse)
def create_experiment(payload: ExperimentCreateRequest, session: Session = Depends(get_db)):
    service = ExperimentService()
    experiment = service.create_experiment(
        session,
        project_id=payload.project_id,
        total_budget=payload.total_budget,
        platforms=[platform.value for platform in payload.platforms],
    )
    return ExperimentResponse(id=experiment.id, status=experiment.status.value)


@router.post("/{experiment_id}/start", response_model=ExperimentResponse)
def start_experiment(experiment_id: int, session: Session = Depends(get_db)):
    service = ExperimentService()
    try:
        experiment = service.start_experiment(session, experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExperimentResponse(id=experiment.id, status=experiment.status.value)


@router.post("/{experiment_id}/close_round", response_model=ExperimentCloseResponse)
def close_round(experiment_id: int):
    result = close_round_task.delay(experiment_id)
    return ExperimentCloseResponse(job_id=result.id)


@router.get("/{experiment_id}/report", response_model=ExperimentReportResponse)
def report(experiment_id: int, session: Session = Depends(get_db)):
    service = ExperimentService()
    try:
        report_data = service.report(session, experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExperimentReportResponse(**report_data)
