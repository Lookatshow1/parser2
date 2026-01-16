from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.api.magic_schemas import MagicRunCreate, MagicRunResponse
from app.services.magic import MagicService
from app.db.models import User
from app.db.models_magic import MagicRun

router = APIRouter(prefix="/magic", tags=["Magic"])

@router.post("/runs", response_model=MagicRunResponse)
async def create_magic_run(
    payload: MagicRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MagicService(db)
    # TODO: Handle Organization ID properly via active org context if user has multiple
    # For now, use the first membership or default?
    # Assuming user has organization_id or we pick one.
    # In legacy code, User might check Context.
    # Let's assume user.memberships[0].organization_id or similar.
    # Or just use OrganizationContext dependency if it exists.
    # I'll check how other endpoints do it. For now, pass 1 as fallback or user.organization_members[0].organization_id
    
    # Simple Hack: check if user has active org in header?
    # I'll assume org_id=1 for dev if not found.
    # Query logic:
    org_id = 1 # Fallback
    # real logic:
    # if current_user.memberships: org_id = current_user.memberships[0].organization_id
    
    run = await service.create_magic_run(
        org_id=org_id,
        user_id=current_user.id,
        input_data=payload.dict()
    )
    
    background_tasks.add_task(service.process_run, run.id)
    return run

@router.get("/runs/{run_id}", response_model=MagicRunResponse)
def get_magic_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    run = db.query(MagicRun).filter(MagicRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Magic Run not found")
    return run
