from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.schemas import (
    PlanCreateRequest,
    PlanListResponse,
    PlanResponse,
    StartTestRequest,
    StartTestResponse,
)
from app.core.config import get_settings
from app.db.models import CampaignPlan
from app.db.session import get_db
from app.services.experiment_engine import ExperimentEngine

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=PlanListResponse)
def list_plans(db: Session = Depends(get_db)):
    plans = db.execute(select(CampaignPlan).order_by(CampaignPlan.id.desc())).scalars().all()
    return PlanListResponse(items=[PlanResponse.model_validate(p, from_attributes=True) for p in plans])


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.get(CampaignPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return PlanResponse.model_validate(plan, from_attributes=True)


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(payload: PlanCreateRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    plan = CampaignPlan(
        organization_id=settings.default_organization_id,
        advertiser_id=payload.advertiser_id,
        name=payload.name,
        platform=payload.platform,
        budget=payload.budget,
        currency=payload.currency,
        start_date=payload.start_date,
        end_date=payload.end_date,
        internal_code=payload.internal_code,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return PlanResponse.model_validate(plan, from_attributes=True)


@router.post("/{plan_id}/start-test", response_model=StartTestResponse)
def start_test(plan_id: int, payload: StartTestRequest, db: Session = Depends(get_db)):
    engine = ExperimentEngine()
    try:
        experiment = engine.start_test(db, plan_id=plan_id, budget=payload.budget)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    creatives_count = db.execute(
        text("SELECT COUNT(*) FROM creative_variants WHERE experiment_id = :experiment_id"),
        {"experiment_id": experiment.id},
    ).scalar_one()

    budgets_count = db.execute(
        text("SELECT COUNT(*) FROM budget_allocations WHERE experiment_id = :experiment_id"),
        {"experiment_id": experiment.id},
    ).scalar_one()

    return StartTestResponse(
        experiment_id=experiment.id,
        creatives_count=int(creatives_count),
        budgets_count=int(budgets_count),
    )
