from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_org, get_current_user
from app.db.session import get_db
from app.db.models import Organization, User, OrgAutomationRun, OrgAutomationAction
from app.api.schemas import (
    AutomationSettingsOut,
    AutomationSettingsUpdate,
    AutomationRunOut,
    AutomationActionOut,
)
from app.services.automation_service import get_or_create_settings, run_automation_for_org
from app.services.automation_executor import execute_action


router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/settings", response_model=AutomationSettingsOut)
def get_automation_settings(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    settings = get_or_create_settings(db, org.id)
    return settings


@router.patch("/settings", response_model=AutomationSettingsOut)
def update_automation_settings(
    item: AutomationSettingsUpdate,
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_or_create_settings(db, org.id)
    if item.is_enabled is not None:
        settings.is_enabled = item.is_enabled
    if item.run_interval_minutes is not None:
        settings.run_interval_minutes = item.run_interval_minutes
    db.commit()
    db.refresh(settings)
    return settings


@router.post("/run", response_model=AutomationRunOut)
def run_automation(
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return run_automation_for_org(db, org, actor_user_id=user.id)


@router.get("/runs", response_model=list[AutomationRunOut])
def list_automation_runs(
    status: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    q = db.query(OrgAutomationRun).filter(OrgAutomationRun.organization_id == org.id)
    if status:
        q = q.filter(OrgAutomationRun.status == status)
    return q.order_by(desc(OrgAutomationRun.created_at)).limit(limit).offset(offset).all()


@router.get("/actions", response_model=list[AutomationActionOut])
def list_automation_actions(
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    q = db.query(OrgAutomationAction).filter(OrgAutomationAction.organization_id == org.id)
    if status:
        q = q.filter(OrgAutomationAction.status == status)
    return q.order_by(desc(OrgAutomationAction.created_at)).limit(limit).offset(offset).all()


@router.post("/actions/{id}/apply", response_model=AutomationActionOut)
def apply_automation_action(
    id: int,
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes the automation action (e.g. stops the campaign).
    """
    # 1. Verify action belongs to org
    action = db.query(OrgAutomationAction).filter(
        OrgAutomationAction.id == id,
        OrgAutomationAction.organization_id == org.id
    ).first()
    
    if not action:
        # 404
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Action not found")
        
    # 2. Execute
    updated_action = execute_action(db, id, user.id)
    return updated_action
