from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.schemas import (
    ExperimentCloseResponse,
    ExperimentCreateRequest,
    ExperimentDetailResponse,
    ExperimentListResponse,
    ExperimentListItem,
    ExperimentReportResponse,
    ExperimentResponse,
)
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
def report(
    experiment_id: int,
    date_from: date | None = Query(None, description="Начало периода (по умолчанию: 7 дней назад)"),
    date_to: date | None = Query(None, description="Конец периода (по умолчанию: сегодня UTC)"),
    session: Session = Depends(get_db),
):
    # Получаем эксперимент и проверяем наличие plan_id
    experiment = session.get(ExperimentModel, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    if experiment.plan_id is None:
        raise HTTPException(status_code=400, detail="Experiment has no plan_id")

    # Устанавливаем дефолтные значения дат (последние 7 дней)
    if date_to is None:
        date_to = datetime.utcnow().date()
    if date_from is None:
        date_from = date_to - timedelta(days=7)

    service = ExperimentService()
    try:
        report_data = service.report(session, experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Запрос метрик с фильтрами по plan_id эксперимента и датам
    query = (
        session.query(
            func.sum(MetricSnapshot.impressions).label("impressions_sum"),
            func.sum(MetricSnapshot.clicks).label("clicks_sum"),
            func.sum(MetricSnapshot.spend).label("spend_sum"),
            func.sum(MetricSnapshot.leads).label("leads_sum"),
            func.sum(MetricSnapshot.purchases).label("purchases_sum"),
            func.sum(MetricSnapshot.revenue).label("revenue_sum"),
        )
        .filter(MetricSnapshot.plan_id == experiment.plan_id)
        .filter(MetricSnapshot.date >= date_from)
        .filter(MetricSnapshot.date <= date_to)
    )

    result = query.first()

    # Если данных нет, возвращаем нули
    if result is None or all(v is None or v == 0 for v in [result.impressions_sum, result.clicks_sum, result.spend_sum]):
        impressions = 0
        clicks = 0
        spend = 0
        leads = 0
        purchases = 0
        revenue = 0
    else:
        impressions = result.impressions_sum or 0
        clicks = result.clicks_sum or 0
        spend = result.spend_sum or 0
        leads = result.leads_sum or 0
        purchases = result.purchases_sum or 0
        revenue = result.revenue_sum or 0

    # Вычисляем производные показатели (безопасное деление на ноль)
    cpc = float(spend / clicks) if clicks > 0 else None
    cpl = float(spend / leads) if leads > 0 else None
    cpa = float(spend / purchases) if purchases > 0 else None

    # Преобразуем rounds для сериализации (datetime -> isoformat)
    rounds_serialized = []
    for round_item in report_data["rounds"]:
        round_dict = round_item.copy() if isinstance(round_item, dict) else {
            "round_index": getattr(round_item, "round_index", None),
            "budget_plan": getattr(round_item, "budget_plan", None),
            "started_at": getattr(round_item, "started_at", None),
            "ended_at": getattr(round_item, "ended_at", None),
        }
        # Сериализуем datetime в строку
        if round_dict.get("started_at") is not None and hasattr(round_dict["started_at"], "isoformat"):
            round_dict["started_at"] = round_dict["started_at"].isoformat()
        if round_dict.get("ended_at") is not None and hasattr(round_dict["ended_at"], "isoformat"):
            round_dict["ended_at"] = round_dict["ended_at"].isoformat()
        rounds_serialized.append(round_dict)

    report_data["rounds"] = rounds_serialized
    report_data["metrics"] = {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "impressions": impressions,
        "clicks": clicks,
        "spend": spend,
        "leads": leads,
        "purchases": purchases,
        "revenue": revenue,
        "cpc": cpc,
        "cpl": cpl,
        "cpa": cpa,
    }
    
    return ExperimentReportResponse(**report_data)
