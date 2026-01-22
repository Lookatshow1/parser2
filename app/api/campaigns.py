from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.api.deps import get_current_membership, get_current_org, get_current_user
from app.api.schemas import (
    CampaignCreateRequest,
    CampaignUpdateRequest,
    CampaignOut,
    CampaignListResponse,
    CampaignSummaryResponse,
    CampaignAdGroupCreateRequest,
    CampaignAdGroupUpdateRequest,
    CampaignAdGroupOut,
    CampaignAdGroupListResponse,
    CampaignAdCreateRequest,
    CampaignAdUpdateRequest,
    CampaignAdOut,
    CampaignAdListResponse,
    CampaignTreeResponse,
    CampaignTree,
    CampaignTreeAdGroup,
    CampaignTreeAd,
    CampaignEventOut,
)
from app.db.models import Campaign, CampaignAdGroup, CampaignAd, CampaignEvent, Organization, Platform, User, CampaignStatus
from app.db.session import get_db
from app.services.rbac import can_read_campaigns, can_write_campaigns
from app.services.campaign_service import cascade_campaign_status

campaigns_router = APIRouter(prefix="/orgs/{org_id}/campaigns", tags=["campaigns"])
ad_groups_router = APIRouter(prefix="/ad-groups", tags=["ad-groups"])
ads_router = APIRouter(prefix="/ads", tags=["ads"])


def _require_read(role: str) -> None:
    if not can_read_campaigns(role):
        raise HTTPException(status_code=403, detail="Недостаточно прав")


def _require_write(role: str) -> None:
    if not can_write_campaigns(role):
        raise HTTPException(status_code=403, detail="Недостаточно прав")


def _ensure_org(org_id: int, org: Organization) -> None:
    if org_id != org.id:
        raise HTTPException(status_code=403, detail="Организация недоступна")


def _get_campaign(db: Session, org_id: int, campaign_id: int) -> Campaign:
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.organization_id == org_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    return campaign


def _get_ad_group(db: Session, org_id: int, group_id: int) -> CampaignAdGroup:
    group = (
        db.query(CampaignAdGroup)
        .join(Campaign, Campaign.id == CampaignAdGroup.campaign_id)
        .filter(CampaignAdGroup.id == group_id, Campaign.organization_id == org_id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return group


def _get_ad(db: Session, org_id: int, ad_id: int) -> CampaignAd:
    ad = (
        db.query(CampaignAd)
        .join(CampaignAdGroup, CampaignAdGroup.id == CampaignAd.ad_group_id)
        .join(Campaign, Campaign.id == CampaignAdGroup.campaign_id)
        .filter(CampaignAd.id == ad_id, Campaign.organization_id == org_id)
        .first()
    )
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return ad


def _log_event(db: Session, org_id: int, entity_type: str, entity_id: int, action: str, user_id: int | None, payload: dict | None = None) -> None:
    event = CampaignEvent(
        organization_id=org_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        payload_json=payload or {},
        created_by_user_id=user_id,
    )
    db.add(event)


def _parse_status(value: str) -> CampaignStatus:
    try:
        return CampaignStatus(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Неверный статус кампании") from exc


def _build_tree(db: Session, campaign: Campaign) -> CampaignTreeResponse:
    groups = (
        db.query(CampaignAdGroup)
        .filter(CampaignAdGroup.campaign_id == campaign.id)
        .order_by(CampaignAdGroup.created_at.asc())
        .all()
    )
    group_ids = [g.id for g in groups]
    ads_by_group: dict[int, list[CampaignAd]] = {g.id: [] for g in groups}
    if group_ids:
        ads = db.query(CampaignAd).filter(CampaignAd.ad_group_id.in_(group_ids)).order_by(CampaignAd.created_at.asc()).all()
        for ad in ads:
            ads_by_group[ad.ad_group_id].append(ad)

    group_models = []
    for group in groups:
        ad_models = [CampaignTreeAd.model_validate(ad, from_attributes=True) for ad in ads_by_group.get(group.id, [])]
        group_models.append(
            CampaignTreeAdGroup(
                **CampaignAdGroupOut.model_validate(group, from_attributes=True).model_dump(),
                ads=ad_models,
            )
        )

    campaign_model = CampaignTree(
        **CampaignOut.model_validate(campaign, from_attributes=True).model_dump(),
        ad_groups=group_models,
    )
    return CampaignTreeResponse(campaign=campaign_model)


@campaigns_router.get("", response_model=CampaignListResponse)
def list_campaigns(
    org_id: int,
    status: Optional[str] = Query(None),
    platform: Optional[Platform] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    _ensure_org(org_id, org)
    query = db.query(Campaign).filter(Campaign.organization_id == org.id)
    if status:
        query = query.filter(Campaign.status == status)
    if platform:
        query = query.filter(Campaign.platform == platform)
    if search:
        query = query.filter(Campaign.name.ilike(f"%{search}%"))
    items = query.order_by(desc(Campaign.created_at)).all()
    return CampaignListResponse(items=items, total=len(items))


@campaigns_router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def create_campaign(
    org_id: int,
    payload: CampaignCreateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    _ensure_org(org_id, org)
    campaign = Campaign(
        organization_id=org.id,
        platform=payload.platform,
        name=payload.name,
        objective=payload.objective,
        status=_parse_status(payload.status),
        budget_total=payload.budget_total,
        budget_daily=payload.budget_daily,
        start_date=payload.start_date,
        end_date=payload.end_date,
        created_by_user_id=user.id,
    )
    db.add(campaign)
    db.flush()
    _log_event(db, org.id, "campaign", campaign.id, "created", user.id, {"name": payload.name})
    db.commit()
    db.refresh(campaign)
    return campaign


@campaigns_router.get("/{campaign_id}", response_model=CampaignSummaryResponse)
def get_campaign(
    org_id: int,
    campaign_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    _ensure_org(org_id, org)
    campaign = _get_campaign(db, org.id, campaign_id)
    ad_groups_count = db.query(func.count(CampaignAdGroup.id)).filter(CampaignAdGroup.campaign_id == campaign.id).scalar() or 0
    ads_count = (
        db.query(func.count(CampaignAd.id))
        .join(CampaignAdGroup, CampaignAdGroup.id == CampaignAd.ad_group_id)
        .filter(CampaignAdGroup.campaign_id == campaign.id)
        .scalar()
        or 0
    )
    payload = CampaignOut.model_validate(campaign, from_attributes=True).model_dump()
    return CampaignSummaryResponse(**payload, ad_groups_count=ad_groups_count, ads_count=ads_count)


@campaigns_router.get("/{campaign_id}/tree", response_model=CampaignTreeResponse)
def get_campaign_tree(
    org_id: int,
    campaign_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    _ensure_org(org_id, org)
    campaign = _get_campaign(db, org.id, campaign_id)
    return _build_tree(db, campaign)


@campaigns_router.get("/{campaign_id}/events", response_model=list[CampaignEventOut])
def list_campaign_events(
    org_id: int,
    campaign_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    _ensure_org(org_id, org)
    _get_campaign(db, org.id, campaign_id)
    events = (
        db.query(CampaignEvent)
        .filter(CampaignEvent.organization_id == org.id, CampaignEvent.entity_type == "campaign", CampaignEvent.entity_id == campaign_id)
        .order_by(desc(CampaignEvent.created_at))
        .all()
    )
    return events


@campaigns_router.patch("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
    org_id: int,
    campaign_id: int,
    payload: CampaignUpdateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    _ensure_org(org_id, org)
    campaign = _get_campaign(db, org.id, campaign_id)
    if payload.platform is not None:
        campaign.platform = payload.platform
    if payload.name is not None:
        campaign.name = payload.name
    if payload.objective is not None:
        campaign.objective = payload.objective
    if payload.status is not None:
        campaign.status = _parse_status(payload.status)
    if payload.budget_total is not None:
        campaign.budget_total = payload.budget_total
    if payload.budget_daily is not None:
        campaign.budget_daily = payload.budget_daily
    if payload.start_date is not None:
        campaign.start_date = payload.start_date
    if payload.end_date is not None:
        campaign.end_date = payload.end_date
    _log_event(db, org.id, "campaign", campaign.id, "updated", user.id)
    db.commit()
    db.refresh(campaign)
    return campaign


@campaigns_router.post("/{campaign_id}/publish", response_model=CampaignOut)
def publish_campaign(
    org_id: int,
    campaign_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    _ensure_org(org_id, org)
    campaign = _get_campaign(db, org.id, campaign_id)
    cascade_campaign_status(db, campaign, CampaignStatus.active, "published", user.id)
    db.commit()
    db.refresh(campaign)
    return campaign


@campaigns_router.post("/{campaign_id}/pause", response_model=CampaignOut)
def pause_campaign(
    org_id: int,
    campaign_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    _ensure_org(org_id, org)
    campaign = _get_campaign(db, org.id, campaign_id)
    cascade_campaign_status(db, campaign, CampaignStatus.paused, "paused", user.id)
    db.commit()
    db.refresh(campaign)
    return campaign


@campaigns_router.post("/{campaign_id}/archive", response_model=CampaignOut)
def archive_campaign(
    org_id: int,
    campaign_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    _ensure_org(org_id, org)
    campaign = _get_campaign(db, org.id, campaign_id)
    cascade_campaign_status(db, campaign, CampaignStatus.archived, "archived", user.id)
    db.commit()
    db.refresh(campaign)
    return campaign


@campaigns_router.delete("/{campaign_id}")
def delete_campaign(
    org_id: int,
    campaign_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    _ensure_org(org_id, org)
    campaign = _get_campaign(db, org.id, campaign_id)
    db.delete(campaign)
    _log_event(db, org.id, "campaign", campaign.id, "deleted", user.id)
    db.commit()
    return {"ok": True}


# --- Ad Groups ---


@ad_groups_router.get("", response_model=CampaignAdGroupListResponse)
def list_ad_groups(
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    query = db.query(CampaignAdGroup).join(Campaign, Campaign.id == CampaignAdGroup.campaign_id).filter(Campaign.organization_id == org.id)
    if campaign_id:
        query = query.filter(CampaignAdGroup.campaign_id == campaign_id)
    items = query.order_by(desc(CampaignAdGroup.created_at)).all()
    return CampaignAdGroupListResponse(items=items, total=len(items))


@ad_groups_router.post("", response_model=CampaignAdGroupOut, status_code=status.HTTP_201_CREATED)
def create_ad_group(
    payload: CampaignAdGroupCreateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    campaign = _get_campaign(db, org.id, payload.campaign_id)
    group = CampaignAdGroup(
        campaign_id=campaign.id,
        name=payload.name,
        status=_parse_status(payload.status),
        bid_strategy=payload.bid_strategy,
        budget_daily=payload.budget_daily,
        targeting_json=payload.targeting_json or {},
    )
    db.add(group)
    db.flush()
    _log_event(db, org.id, "ad_group", group.id, "created", user.id, {"campaign_id": campaign.id})
    db.commit()
    db.refresh(group)
    return group


@ad_groups_router.get("/{group_id}", response_model=CampaignAdGroupOut)
def get_ad_group(
    group_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    return _get_ad_group(db, org.id, group_id)


@ad_groups_router.patch("/{group_id}", response_model=CampaignAdGroupOut)
def update_ad_group(
    group_id: int,
    payload: CampaignAdGroupUpdateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    group = _get_ad_group(db, org.id, group_id)
    if payload.name is not None:
        group.name = payload.name
    if payload.status is not None:
        group.status = _parse_status(payload.status)
    if payload.bid_strategy is not None:
        group.bid_strategy = payload.bid_strategy
    if payload.budget_daily is not None:
        group.budget_daily = payload.budget_daily
    if payload.targeting_json is not None:
        group.targeting_json = payload.targeting_json
    _log_event(db, org.id, "ad_group", group.id, "updated", user.id)
    db.commit()
    db.refresh(group)
    return group


@ad_groups_router.delete("/{group_id}")
def delete_ad_group(
    group_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    group = _get_ad_group(db, org.id, group_id)
    db.delete(group)
    _log_event(db, org.id, "ad_group", group.id, "deleted", user.id)
    db.commit()
    return {"ok": True}


# --- Ads ---


@ads_router.get("", response_model=CampaignAdListResponse)
def list_ads(
    ad_group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    query = (
        db.query(CampaignAd)
        .join(CampaignAdGroup, CampaignAdGroup.id == CampaignAd.ad_group_id)
        .join(Campaign, Campaign.id == CampaignAdGroup.campaign_id)
        .filter(Campaign.organization_id == org.id)
    )
    if ad_group_id:
        query = query.filter(CampaignAd.ad_group_id == ad_group_id)
    items = query.order_by(desc(CampaignAd.created_at)).all()
    return CampaignAdListResponse(items=items, total=len(items))


@ads_router.post("", response_model=CampaignAdOut, status_code=status.HTTP_201_CREATED)
def create_ad(
    payload: CampaignAdCreateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    group = _get_ad_group(db, org.id, payload.ad_group_id)
    ad = CampaignAd(
        ad_group_id=group.id,
        name=payload.name,
        status=_parse_status(payload.status),
        creative_json=payload.creative_json or {},
        landing_url=payload.landing_url,
    )
    db.add(ad)
    db.flush()
    _log_event(db, org.id, "ad", ad.id, "created", user.id, {"ad_group_id": group.id})
    db.commit()
    db.refresh(ad)
    return ad


@ads_router.get("/{ad_id}", response_model=CampaignAdOut)
def get_ad(
    ad_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    return _get_ad(db, org.id, ad_id)


@ads_router.patch("/{ad_id}", response_model=CampaignAdOut)
def update_ad(
    ad_id: int,
    payload: CampaignAdUpdateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    ad = _get_ad(db, org.id, ad_id)
    if payload.name is not None:
        ad.name = payload.name
    if payload.status is not None:
        ad.status = _parse_status(payload.status)
    if payload.creative_json is not None:
        ad.creative_json = payload.creative_json
    if payload.landing_url is not None:
        ad.landing_url = payload.landing_url
    _log_event(db, org.id, "ad", ad.id, "updated", user.id)
    db.commit()
    db.refresh(ad)
    return ad


@ads_router.delete("/{ad_id}")
def delete_ad(
    ad_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    ad = _get_ad(db, org.id, ad_id)
    db.delete(ad)
    _log_event(db, org.id, "ad", ad.id, "deleted", user.id)
    db.commit()
    return {"ok": True}
