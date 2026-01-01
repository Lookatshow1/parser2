from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import PlanCreateRequest, PlanResponse, StartTestResponse
from app.db.models import CampaignPlan
from app.db.session import get_db
from app.services.experiment_engine import ExperimentEngine

router = APIRouter(prefix="/plans")


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
    budget: int = Query(..., gt=0),
    session: Session = Depends(get_db),
):
    engine = ExperimentEngine()
    try:
        experiment = engine.start_test(session, plan_id=plan_id, budget=budget)
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
