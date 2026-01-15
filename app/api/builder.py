from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from urllib.parse import urlparse

from app.api.deps import get_current_org
from app.api.schemas import (
    BuilderCampaignCreateRequest,
    BuilderCampaignUpdateRequest,
    BuilderCampaignOut,
    BuilderAdGroupCreateRequest,
    BuilderAdGroupUpdateRequest,
    BuilderAdGroupOut,
    BuilderAdCreateRequest,
    BuilderAdUpdateRequest,
    BuilderAdOut,
    BuilderTreeResponse,
    BuilderTreeCampaign,
    BuilderTreeAdGroup,
    BuilderTreeAd
)
from app.db.models import (
    Organization,
    Experiment,
    BuilderCampaign,
    BuilderAdGroup,
    BuilderAd,
    OrgAuditEvent,
    OrgUtmSettings,
    CampaignPlan
)
from app.db.session import get_db
from app.utils.utm import build_utm_url, build_utm_from_org_settings

router = APIRouter(tags=["builder"])

# --- Helper ---

def get_experiment_or_404(db: Session, experiment_id: int, org_id: int) -> Experiment:
    exp = db.query(Experiment).filter(
        Experiment.id == experiment_id,
        Experiment.organization_id == org_id
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp

def log_audit(db: Session, org_id: int, action: str, subject_type: str, subject_id: int, meta: dict):
    event = OrgAuditEvent(
        organization_id=org_id,
        action=action,
        subject_type=subject_type,
        subject_id=subject_id,
        meta=meta
    )
    db.add(event)
    # Commit is usually handled by the caller or at the end of request

# --- Campaigns ---

@router.get("/experiments/{experiment_id}/builder/campaigns", response_model=list[BuilderCampaignOut])
def list_builder_campaigns(
    experiment_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    get_experiment_or_404(db, experiment_id, org.id)
    items = db.query(BuilderCampaign).filter(
        BuilderCampaign.experiment_id == experiment_id,
        BuilderCampaign.organization_id == org.id
    ).all()
    return items

@router.post("/experiments/{experiment_id}/builder/campaigns", response_model=BuilderCampaignOut)
def create_builder_campaign(
    experiment_id: int,
    item: BuilderCampaignCreateRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    get_experiment_or_404(db, experiment_id, org.id)
    campaign = BuilderCampaign(
        organization_id=org.id,
        experiment_id=experiment_id,
        platform=item.platform,
        name=item.name,
        status=item.status
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    log_audit(db, org.id, "campaign_created", "builder_campaign", campaign.id, {"name": campaign.name})
    db.commit()
    return campaign

@router.post("/plans/{plan_id}/builder/campaigns", response_model=BuilderCampaignOut)
def create_builder_campaign_for_plan(
    plan_id: int,
    item: BuilderCampaignCreateRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Создать кампанию напрямую в плане (без эксперимента)"""
    plan = db.query(CampaignPlan).filter(
        CampaignPlan.id == plan_id,
        CampaignPlan.organization_id == org.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="План не найден")
    
    campaign = BuilderCampaign(
        organization_id=org.id,
        plan_id=plan_id,
        platform=item.platform,
        name=item.name,
        status=item.status
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    log_audit(db, org.id, "campaign_created", "builder_campaign", campaign.id, {"name": campaign.name, "plan_id": plan_id})
    db.commit()
    return campaign

@router.patch("/builder/campaigns/{campaign_id}", response_model=BuilderCampaignOut)
def update_builder_campaign(
    campaign_id: int,
    item: BuilderCampaignUpdateRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    campaign = db.query(BuilderCampaign).filter(
        BuilderCampaign.id == campaign_id,
        BuilderCampaign.organization_id == org.id
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if item.name is not None:
        campaign.name = item.name
    if item.status is not None:
        campaign.status = item.status

    db.commit()
    db.refresh(campaign)
    log_audit(db, org.id, "campaign_updated", "builder_campaign", campaign.id, {"name": campaign.name})
    db.commit()
    return campaign

@router.delete("/builder/campaigns/{campaign_id}")
def delete_builder_campaign(
    campaign_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    campaign = db.query(BuilderCampaign).filter(
        BuilderCampaign.id == campaign_id,
        BuilderCampaign.organization_id == org.id
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db.delete(campaign)
    log_audit(db, org.id, "campaign_deleted", "builder_campaign", campaign_id, {"name": campaign.name})
    db.commit()
    return {"ok": True}

# --- Ad Groups ---

@router.get("/builder/campaigns/{campaign_id}/ad-groups", response_model=list[BuilderAdGroupOut])
def list_builder_ad_groups(
    campaign_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    # Ensure campaign belongs to org
    campaign = db.query(BuilderCampaign).filter(
        BuilderCampaign.id == campaign_id,
        BuilderCampaign.organization_id == org.id
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    items = db.query(BuilderAdGroup).filter(
        BuilderAdGroup.campaign_id == campaign_id,
        BuilderAdGroup.organization_id == org.id
    ).all()
    return items

@router.post("/builder/campaigns/{campaign_id}/ad-groups", response_model=BuilderAdGroupOut)
def create_builder_ad_group(
    campaign_id: int,
    item: BuilderAdGroupCreateRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    campaign = db.query(BuilderCampaign).filter(
        BuilderCampaign.id == campaign_id,
        BuilderCampaign.organization_id == org.id
    ).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    group = BuilderAdGroup(
        organization_id=org.id,
        campaign_id=campaign_id,
        name=item.name,
        status=item.status
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    log_audit(db, org.id, "ad_group_created", "builder_ad_group", group.id, {"name": group.name})
    db.commit()
    return group

@router.patch("/builder/ad-groups/{group_id}", response_model=BuilderAdGroupOut)
def update_builder_ad_group(
    group_id: int,
    item: BuilderAdGroupUpdateRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    group = db.query(BuilderAdGroup).filter(
        BuilderAdGroup.id == group_id,
        BuilderAdGroup.organization_id == org.id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Ad group not found")

    if item.name is not None:
        group.name = item.name
    if item.status is not None:
        group.status = item.status

    db.commit()
    db.refresh(group)
    log_audit(db, org.id, "ad_group_updated", "builder_ad_group", group.id, {"name": group.name})
    db.commit()
    return group

@router.delete("/builder/ad-groups/{group_id}")
def delete_builder_ad_group(
    group_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    group = db.query(BuilderAdGroup).filter(
        BuilderAdGroup.id == group_id,
        BuilderAdGroup.organization_id == org.id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Ad group not found")

    db.delete(group)
    log_audit(db, org.id, "ad_group_deleted", "builder_ad_group", group_id, {"name": group.name})
    db.commit()
    return {"ok": True}

# --- Ads ---

@router.get("/builder/ad-groups/{group_id}/ads", response_model=list[BuilderAdOut])
def list_builder_ads(
    group_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    group = db.query(BuilderAdGroup).filter(
        BuilderAdGroup.id == group_id,
        BuilderAdGroup.organization_id == org.id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Ad group not found")

    items = db.query(BuilderAd).filter(
        BuilderAd.ad_group_id == group_id,
        BuilderAd.organization_id == org.id
    ).all()
    return items

@router.post("/builder/ad-groups/{group_id}/ads", response_model=BuilderAdOut)
def create_builder_ad(
    group_id: int,
    item: BuilderAdCreateRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    group = db.query(BuilderAdGroup).filter(
        BuilderAdGroup.id == group_id,
        BuilderAdGroup.organization_id == org.id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Ad group not found")

    # Get organization UTM settings for automatic generation
    utm_settings = db.query(OrgUtmSettings).filter(OrgUtmSettings.organization_id == org.id).first()
    
    # Get campaign and plan for template replacements
    campaign = db.query(BuilderCampaign).filter(BuilderCampaign.id == group.campaign_id).first()
    platform = campaign.platform if campaign else None
    
    # Validate URL if present and build final_url
    final_url = None
    if item.base_url:
        try:
            parsed = urlparse(item.base_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL")
            
            # Use org settings if available, otherwise use custom utm_json
            if utm_settings and platform:
                final_url = build_utm_from_org_settings(
                    base_url=item.base_url,
                    org_settings=utm_settings,
                    platform=platform,
                    campaign_id=campaign.external_id or str(campaign.id),
                    ad_group_id=group.external_id or str(group.id),
                    ad_id=None,  # ad_id will be set after creation
                    custom_utm=item.utm_json if item.utm_json else None
                )
            else:
                # Fallback to manual UTM building
                final_url = build_utm_url(item.base_url, item.utm_json or {})
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid base_url")

    ad = BuilderAd(
        organization_id=org.id,
        ad_group_id=group_id,
        name=item.name,
        title=item.title,
        text=item.text,
        base_url=item.base_url,
        utm_json=item.utm_json,
        final_url=final_url,
        status=item.status
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)
    log_audit(db, org.id, "ad_created", "builder_ad", ad.id, {"name": ad.name})
    db.commit()
    return ad

@router.patch("/builder/ads/{ad_id}", response_model=BuilderAdOut)
def update_builder_ad(
    ad_id: int,
    item: BuilderAdUpdateRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    ad = db.query(BuilderAd).filter(
        BuilderAd.id == ad_id,
        BuilderAd.organization_id == org.id
    ).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if item.name is not None:
        ad.name = item.name
    if item.title is not None:
        ad.title = item.title
    if item.text is not None:
        ad.text = item.text
    if item.status is not None:
        ad.status = item.status

    # Get organization UTM settings for automatic generation
    utm_settings = db.query(OrgUtmSettings).filter(OrgUtmSettings.organization_id == org.id).first()
    
    # Get campaign and plan for template replacements
    group = db.query(BuilderAdGroup).filter(BuilderAdGroup.id == ad.ad_group_id).first()
    campaign = group.campaign if group else None
    platform = campaign.platform if campaign else None
    
    # Recalculate final_url if base_url or utm_json changes
    new_base_url = item.base_url if item.base_url is not None else ad.base_url
    new_utm_json = item.utm_json if item.utm_json is not None else ad.utm_json

    if item.base_url is not None or item.utm_json is not None:
        if new_base_url:
            try:
                parsed = urlparse(new_base_url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError("Invalid URL")
                
                # Use org settings if available
                if utm_settings and platform and group:
                    ad.final_url = build_utm_from_org_settings(
                        base_url=new_base_url,
                        org_settings=utm_settings,
                        platform=platform,
                        campaign_id=campaign.external_id or str(campaign.id) if campaign else None,
                        ad_group_id=group.external_id or str(group.id) if group else None,
                        ad_id=ad.external_id or str(ad.id),
                        custom_utm=new_utm_json if new_utm_json else None
                    )
                else:
                    # Fallback to manual UTM building
                    ad.final_url = build_utm_url(new_base_url, new_utm_json or {})
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid base_url")
        else:
            ad.final_url = None

    if item.base_url is not None:
        ad.base_url = item.base_url
    if item.utm_json is not None:
        ad.utm_json = item.utm_json

    db.commit()
    db.refresh(ad)
    log_audit(db, org.id, "ad_updated", "builder_ad", ad.id, {"name": ad.name})
    db.commit()
    return ad

@router.delete("/builder/ads/{ad_id}")
def delete_builder_ad(
    ad_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    ad = db.query(BuilderAd).filter(
        BuilderAd.id == ad_id,
        BuilderAd.organization_id == org.id
    ).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    db.delete(ad)
    log_audit(db, org.id, "ad_deleted", "builder_ad", ad_id, {"name": ad.name})
    db.commit()
    return {"ok": True}

# --- Tree ---

@router.get("/experiments/{experiment_id}/builder/tree", response_model=BuilderTreeResponse)
def get_builder_tree(
    experiment_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    get_experiment_or_404(db, experiment_id, org.id)

    # Fetch all campaigns with nested groups and ads
    # Using joinedload for efficiency
    campaigns = db.query(BuilderCampaign).filter(
        BuilderCampaign.experiment_id == experiment_id,
        BuilderCampaign.organization_id == org.id
    ).options(
        joinedload(BuilderCampaign.ad_groups).joinedload(BuilderAdGroup.ads)
    ).all()

    # Transform to Pydantic models (SQLAlchemy models to Pydantic is handled by from_attributes=True,
    # but we need to ensure structure matches BuilderTreeResponse)

    result_campaigns = []
    for c in campaigns:
        c_model = BuilderTreeCampaign.model_validate(c)
        # Manually populate nested lists if needed, but joinedload + Pydantic should handle it if names match.
        # SQLAlchemy relationship names: ad_groups, ads. Pydantic names: ad_groups, ads.
        # It should work automatically.
        result_campaigns.append(c_model)

    return {"campaigns": result_campaigns}
