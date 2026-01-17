"""
Magic API Endpoints

Public and authenticated endpoints for AI ad generation.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.api.deps import get_db, get_current_user, get_current_org_id
from app.api.magic_schemas import MagicRunCreate, MagicRunResponse
from app.services.magic import MagicService
from app.db.models import User
from app.db.models_magic import MagicRun

router = APIRouter(prefix="/magic", tags=["Magic"])


# =============================================================================
# PUBLIC SCHEMAS (no auth required)
# =============================================================================

class PublicGenerateRequest(BaseModel):
    """Request for public creative generation."""
    landing_url: Optional[str] = None
    description: Optional[str] = None


class AdCreative(BaseModel):
    title: str
    text: str
    approach: str


class ImageCreative(BaseModel):
    url: str
    prompt: str
    theme: str


class PublicGenerateResponse(BaseModel):
    """Response with generated creatives."""
    business_name: str
    business_type: str
    ads: List[AdCreative]
    images: List[ImageCreative]


class SaveCreativesRequest(BaseModel):
    """Request to save creatives after registration."""
    creatives: Dict[str, Any]
    landing_url: Optional[str] = ""


class SaveCreativesResponse(BaseModel):
    campaign_id: int
    message: str


# =============================================================================
# PUBLIC ENDPOINTS (no auth - for landing page)
# =============================================================================

@router.post("/generate-public", response_model=PublicGenerateResponse)
async def generate_public(
    payload: PublicGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Публичный endpoint для генерации креативов БЕЗ авторизации.
    Используется на главной странице.
    """
    service = MagicService(db)
    
    result = await service.generate_creatives_public(
        input_text=payload.description or "",
        landing_url=payload.landing_url
    )
    
    return result


# =============================================================================
# AUTHENTICATED ENDPOINTS
# =============================================================================

@router.post("/save-creatives", response_model=SaveCreativesResponse)
async def save_creatives(
    payload: SaveCreativesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id)
):
    """
    Сохранить сгенерированные креативы как черновик кампании.
    Вызывается после регистрации пользователя.
    """
    service = MagicService(db)
    
    campaign = service.create_drafts_from_public(
        org_id=org_id,
        user_id=current_user.id,
        creatives=payload.creatives,
        landing_url=payload.landing_url
    )
    
    return SaveCreativesResponse(
        campaign_id=campaign.id,
        message="Кампания создана! Осталось пополнить баланс для запуска."
    )


@router.post("/runs", response_model=MagicRunResponse)
async def create_magic_run(
    payload: MagicRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id)
):
    """Создать Magic Run для полной генерации кампании."""
    service = MagicService(db)
    
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
    """Получить статус Magic Run."""
    run = db.query(MagicRun).filter(MagicRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Magic Run not found")
    return run
