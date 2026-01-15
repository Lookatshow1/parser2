"""
API для Студии кампаний - работа с планами и builder кампаниями напрямую
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional
import json
import csv
import io

from app.api.deps import get_current_org
from app.db.models import (
    Organization,
    CampaignPlan,
    BuilderCampaign,
    BuilderAdGroup,
    BuilderAd,
    OrgAuditEvent,
    Connection,
    CampaignPlanStatus
)
from app.db.session import get_db
from app.api.schemas import (
    PlanResponse,
    BuilderCampaignOut,
    BuilderAdGroupOut,
    BuilderAdOut,
)

router = APIRouter(prefix="/studio", tags=["studio"])


def log_audit(db: Session, org_id: int, action: str, subject_type: str, subject_id: int, meta: dict):
    """Логирование действий в аудит"""
    event = OrgAuditEvent(
        organization_id=org_id,
        action=action,
        subject_type=subject_type,
        subject_id=subject_id,
        meta=meta
    )
    db.add(event)


# --- Plans ---

@router.get("/plans", response_model=list[PlanResponse])
def list_plans(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Список планов организации"""
    plans = db.query(CampaignPlan).filter(
        CampaignPlan.organization_id == org.id
    ).order_by(CampaignPlan.created_at.desc()).all()
    return [PlanResponse.model_validate(p, from_attributes=True) for p in plans]


@router.post("/plans", response_model=PlanResponse, status_code=201)
def create_plan(
    name: str,
    connection_id: int,
    platform: str,
    org: Organization = Depends(get_current_org),
    budget: Optional[float] = None,
    currency: str = "RUB",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Создать план"""
    # Проверка подключения
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.organization_id == org.id
    ).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Подключение не найдено")
    
    # Получаем advertiser_id из connection (если есть) или создаём дефолтный
    from app.core.config import get_settings
    settings = get_settings()
    
    # Для MVP используем дефолтный advertiser_id
    plan = CampaignPlan(
        organization_id=org.id,
        advertiser_id=settings.default_organization_id,  # TODO: получить из connection
        connection_id=connection_id,
        name=name,
        platform=platform,
        budget=budget,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
        status=CampaignPlanStatus.draft
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    log_audit(db, org.id, "plan_created", "campaign_plan", plan.id, {"name": plan.name})
    db.commit()
    
    return PlanResponse.model_validate(plan, from_attributes=True)


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Получить план"""
    plan = db.query(CampaignPlan).filter(
        CampaignPlan.id == plan_id,
        CampaignPlan.organization_id == org.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="План не найден")
    return PlanResponse.model_validate(plan, from_attributes=True)


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    name: Optional[str] = None,
    status: Optional[str] = None,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Обновить план"""
    plan = db.query(CampaignPlan).filter(
        CampaignPlan.id == plan_id,
        CampaignPlan.organization_id == org.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="План не найден")
    
    if name is not None:
        plan.name = name
    if status is not None:
        plan.status = CampaignPlanStatus(status)
    
    db.commit()
    db.refresh(plan)
    
    log_audit(db, org.id, "plan_updated", "campaign_plan", plan.id, {"name": plan.name})
    db.commit()
    
    return PlanResponse.model_validate(plan, from_attributes=True)


# --- Builder Campaigns under Plans ---

@router.get("/plans/{plan_id}/campaigns", response_model=list[BuilderCampaignOut])
def list_plan_campaigns(
    plan_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Список кампаний плана"""
    plan = db.query(CampaignPlan).filter(
        CampaignPlan.id == plan_id,
        CampaignPlan.organization_id == org.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="План не найден")
    
    campaigns = db.query(BuilderCampaign).filter(
        BuilderCampaign.plan_id == plan_id,
        BuilderCampaign.organization_id == org.id
    ).all()
    return [BuilderCampaignOut.model_validate(c, from_attributes=True) for c in campaigns]


@router.post("/plans/{plan_id}/campaigns", response_model=BuilderCampaignOut, status_code=201)
def create_plan_campaign(
    plan_id: int,
    name: str,
    platform: str,
    org: Organization = Depends(get_current_org),
    status: str = "draft",
    daily_budget: Optional[float] = None,
    total_budget: Optional[float] = None,
    goal: Optional[str] = None,
    external_ref: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Создать кампанию в плане"""
    plan = db.query(CampaignPlan).filter(
        CampaignPlan.id == plan_id,
        CampaignPlan.organization_id == org.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="План не найден")
    
    campaign = BuilderCampaign(
        organization_id=org.id,
        plan_id=plan_id,
        platform=platform,
        name=name,
        status=status,
        daily_budget=daily_budget,
        total_budget=total_budget,
        goal=goal,
        external_ref=external_ref
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    log_audit(db, org.id, "campaign_created", "builder_campaign", campaign.id, {"name": campaign.name, "plan_id": plan_id})
    db.commit()
    
    return BuilderCampaignOut.model_validate(campaign, from_attributes=True)


# --- Export ---

@router.get("/plans/{plan_id}/export")
def export_plan(
    plan_id: int,
    format: str = Query("json", regex="^(json|csv)$"),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Экспорт плана в JSON или CSV"""
    plan = db.query(CampaignPlan).filter(
        CampaignPlan.id == plan_id,
        CampaignPlan.organization_id == org.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="План не найден")
    
    # Загружаем все данные плана
    campaigns = db.query(BuilderCampaign).filter(
        BuilderCampaign.plan_id == plan_id,
        BuilderCampaign.organization_id == org.id
    ).options(
        joinedload(BuilderCampaign.ad_groups).joinedload(BuilderAdGroup.ads)
    ).all()
    
    # Формируем структуру данных
    export_data = {
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "platform": plan.platform.value,
            "budget": float(plan.budget) if plan.budget else None,
            "currency": plan.currency,
            "start_date": plan.start_date.isoformat() if plan.start_date else None,
            "end_date": plan.end_date.isoformat() if plan.end_date else None,
            "status": plan.status.value
        },
        "campaigns": []
    }
    
    for campaign in campaigns:
        campaign_data = {
            "id": campaign.id,
            "name": campaign.name,
            "platform": campaign.platform.value,
            "status": campaign.status,
            "daily_budget": float(campaign.daily_budget) if campaign.daily_budget else None,
            "total_budget": float(campaign.total_budget) if campaign.total_budget else None,
            "goal": campaign.goal,
            "external_ref": campaign.external_ref,
            "ad_groups": []
        }
        
        for group in campaign.ad_groups:
            group_data = {
                "id": group.id,
                "name": group.name,
                "status": group.status,
                "bid": float(group.bid) if group.bid else None,
                "targeting": group.targeting_json,
                "ads": []
            }
            
            for ad in group.ads:
                ad_data = {
                    "id": ad.id,
                    "name": ad.name,
                    "title": ad.title,
                    "text": ad.text,
                    "base_url": ad.base_url,
                    "final_url": ad.final_url,
                    "utm_json": ad.utm_json,
                    "status": ad.status
                }
                group_data["ads"].append(ad_data)
            
            campaign_data["ad_groups"].append(group_data)
        
        export_data["campaigns"].append(campaign_data)
    
    # Экспорт
    if format == "json":
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            io.BytesIO(json_str.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="plan_{plan_id}.json"'}
        )
    else:  # CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow(["План", "Кампания", "Группа", "Объявление", "URL", "Статус"])
        
        # Данные
        for campaign in campaigns:
            for group in campaign.ad_groups:
                for ad in group.ads:
                    writer.writerow([
                        plan.name,
                        campaign.name,
                        group.name,
                        ad.name or ad.title or "",
                        ad.final_url or ad.base_url or "",
                        ad.status
                    ])
        
        csv_str = output.getvalue()
        return StreamingResponse(
            io.BytesIO(csv_str.encode('utf-8-sig')),  # BOM для Excel
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="plan_{plan_id}.csv"'}
        )
