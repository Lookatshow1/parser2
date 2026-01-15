from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_org, get_current_user
from app.api.schemas import ChangePlanOut, ChangePlanItemOut
from pydantic import BaseModel
from app.db.models import Organization, User, ChangePlan, ChangePlanItem
from app.db.session import get_db
from app.services.change_plans_service import create_plan, add_item, set_plan_status, execute_plan
router = APIRouter(prefix="/change-plans", tags=["change-plans"])

class CreatePlanRequest(BaseModel):
    connection_id: int
    title: str
    date_from: date | None = None
    date_to: date | None = None

class AddItemRequest(BaseModel):
    subject_type: str
    subject_id: int
    action_type: str
    params: dict = {}

@router.get("", response_model=list[ChangePlanOut])
def list_plans(
    connection_id: int | None = None,
    status: str | None = None,
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    q = db.query(ChangePlan).filter(ChangePlan.organization_id == org.id)
    if connection_id:
        q = q.filter(ChangePlan.connection_id == connection_id)
    if status:
        q = q.filter(ChangePlan.status == status)

    return q.order_by(desc(ChangePlan.created_at)).limit(limit).offset(offset).all()

@router.post("", response_model=ChangePlanOut)
def create_change_plan(
    body: CreatePlanRequest,
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_plan(db, org.id, user.id, body.connection_id, body.title, body.date_from, body.date_to)

@router.get("/{plan_id}", response_model=ChangePlanOut)
def get_plan(
    plan_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    plan = db.query(ChangePlan).filter(ChangePlan.id == plan_id, ChangePlan.organization_id == org.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="План не найден")
    return plan

@router.post("/{plan_id}/items", response_model=ChangePlanItemOut)
def add_plan_item(
    plan_id: int,
    body: AddItemRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    return add_item(db, org.id, plan_id, body.subject_type, body.subject_id, body.action_type, body.params)

@router.post("/{plan_id}/ready")
def mark_ready(
    plan_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    set_plan_status(db, org.id, plan_id, "ready")
    return {"status": "ready"}

@router.post("/{plan_id}/apply")
def apply_plan_endpoint(
    plan_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    execute_plan(db, org.id, plan_id)
    return {"status": "applying"}
