from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import (
    PlanCreateRequest,
    PlanListResponse,
    PlanResponse,
    StartTestRequest,
    StartTestResponse,
)
from app.db.models import CampaignPlan
from app.db.session import get_db
from app.services.experiment_engine import ExperimentEngine

router = APIRouter(prefix="/plans")


@router.get("", response_model=PlanListResponse)
def list_plans(session: Session = Depends(get_db)):
    plans = session.query(CampaignPlan).all()
    return PlanListResponse(
        items=[PlanResponse(id=plan.id, url=plan.url, internal_code=plan.internal_code) for plan in plans]
    )


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, session: Session = Depends(get_db)):
    plan = session.get(CampaignPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return PlanResponse(id=plan.id, url=plan.url, internal_code=plan.internal_code)


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(payload: PlanCreateRequest, session: Session = Depends(get_db)):
    plan = CampaignPlan(
        url=payload.url,
        business_description=payload.business_description,
        kpi=payload.kpi,
        internal_code=payload.internal_code,
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return PlanResponse(id=plan.id, url=plan.url, internal_code=plan.internal_code)


@router.post("/{plan_id}/start_test", response_model=StartTestResponse)
def start_test(
    plan_id: int,
    payload: StartTestRequest,
    session: Session = Depends(get_db),
):
    engine = ExperimentEngine()
    try:
        experiment = engine.start_test(session, plan_id=plan_id, budget=payload.budget)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    creatives_count = session.execute(
        text("SELECT COUNT(*) FROM creative_variants WHERE experiment_id = :experiment_id"),
        {"experiment_id": experiment.id},
    ).scalar_one()
    budgets_count = session.execute(
        text("SELECT COUNT(*) FROM budget_allocations WHERE experiment_id = :experiment_id"),
        {"experiment_id": experiment.id},
    ).scalar_one()
    return StartTestResponse(
        experiment_id=experiment.id,
        creatives_count=creatives_count,
        budgets_count=budgets_count,
    )
