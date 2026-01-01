from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    ExperimentCloseResponse,
    ExperimentCreateRequest,
    ExperimentDetailResponse,
    ExperimentListResponse,
    ExperimentListItem,
    ExperimentReportResponse,
    ExperimentResponse,
)
from sqlalchemy import func

from app.db.models import Experiment as ExperimentModel, MetricSnapshot
from app.db.session import get_db
from app.services.experiment_service import ExperimentService
from app.workers.experiment_tasks import close_round_task

router = APIRouter(prefix="/experiments")


@router.get("", response_model=ExperimentListResponse)
def list_experiments(session: Session = Depends(get_db)):
    experiments = session.query(ExperimentModel).all()
    return ExperimentListResponse(
        items=[
            ExperimentListItem(
                id=item.id,
                status=item.status.value,
                plan_id=item.plan_id,
                total_budget=item.total_budget,
            )
            for item in experiments
        ]
    )


@router.post("", response_model=ExperimentResponse)
def create_experiment(payload: ExperimentCreateRequest, session: Session = Depends(get_db)):
    service = ExperimentService()
    experiment = service.create_experiment(
        session,
        plan_id=payload.plan_id,
        total_budget=payload.budget,
        platforms=[platform.value for platform in payload.platforms] if payload.platforms else None,
    )
    return ExperimentResponse(id=experiment.id, status=experiment.status.value)


@router.post("/create", response_model=ExperimentResponse, deprecated=True)
def create_experiment_legacy(payload: ExperimentCreateRequest, session: Session = Depends(get_db)):
    service = ExperimentService()
    experiment = service.create_experiment(
        session,
        plan_id=payload.plan_id,
        total_budget=payload.budget,
        platforms=[platform.value for platform in payload.platforms] if payload.platforms else None,
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


@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
def get_experiment(experiment_id: int, session: Session = Depends(get_db)):
    experiment = session.get(ExperimentModel, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return ExperimentDetailResponse(
        id=experiment.id,
        status=experiment.status.value,
        plan_id=experiment.plan_id,
        total_budget=experiment.total_budget,
        platforms=experiment.platforms,
    )


@router.get("/{experiment_id}/report", response_model=ExperimentReportResponse)
def report(experiment_id: int, session: Session = Depends(get_db)):
    service = ExperimentService()
    try:
        report_data = service.report(session, experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    metrics = (
        session.query(
            MetricSnapshot.date,
            MetricSnapshot.platform,
            func.sum(MetricSnapshot.impressions).label("impressions_sum"),
            func.sum(MetricSnapshot.clicks).label("clicks_sum"),
            func.sum(MetricSnapshot.spend).label("spend_sum"),
        )
        .group_by(MetricSnapshot.date, MetricSnapshot.platform)
        .all()
    )
    report_data["metrics"] = [
        {
            "date": metric.date.isoformat(),
            "platform": metric.platform.value,
            "impressions": metric.impressions_sum,
            "clicks": metric.clicks_sum,
            "spend": metric.spend_sum,
        }
        for metric in metrics
    ]
    return ExperimentReportResponse(**report_data)
