from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case, and_, or_, exists, cast, String

from app.api.deps import get_current_membership, get_current_org, get_current_user
from app.db.models import (
    Organization,
    Connection,
    AdCampaign,
    AdAdGroup,
    AdAd,
    OrgUtmSettings,
    OrgUtmRule,
    User,
    ConversionEvent,
    ConversionEventType,
    CampaignPlan,
)
from app.db.session import get_db
from app.api.schemas import (
    AdCampaignOut, AdAdGroupOut, AdAdOut,
    UtmSettingsOut, UtmSettingsUpdate, UtmBuildRequest, UtmBuildResponse,
    UtmRuleOut, UtmRuleCreate, UtmRuleUpdate, UtmStatusOut,
    UtmReportResponse, UtmReportItem, UtmReportTotals,
)
from app.services.utm_reconcile_service import reconcile_ads_utm_for_connection, get_utm_status_for_connection
from app.services.utm_service import build_utm_params, apply_utm, normalize_and_validate_url
from app.services.audit import log_org_event
from app.services.rbac import can_read_campaigns, can_write_campaigns

router = APIRouter(tags=["catalog"])

# --- Catalog Read API ---

def _require_read(role: str) -> None:
    if not can_read_campaigns(role):
        raise HTTPException(status_code=403, detail="Недостаточно прав")


def _require_write(role: str) -> None:
    if not can_write_campaigns(role):
        raise HTTPException(status_code=403, detail="Недостаточно прав")

@router.get("/connections/{connection_id}/campaigns", response_model=list[AdCampaignOut])
def list_catalog_campaigns(
    connection_id: int,
    query: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    _require_read(membership.role)
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение не найдено")

    q = db.query(AdCampaign).filter(AdCampaign.connection_id == connection_id)
    if query:
        q = q.filter(AdCampaign.name.ilike(f"%{query}%"))

    items = q.order_by(desc(AdCampaign.updated_at)).limit(limit).offset(offset).all()
    return items

@router.get("/connections/{connection_id}/ad-groups", response_model=list[AdAdGroupOut])
def list_catalog_ad_groups(
    connection_id: int,
    campaign_external_id: str | None = None,
    query: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    _require_read(membership.role)
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение не найдено")

    q = db.query(AdAdGroup).filter(AdAdGroup.connection_id == connection_id)
    if campaign_external_id:
        q = q.filter(AdAdGroup.campaign_external_id == campaign_external_id)
    if query:
        q = q.filter(AdAdGroup.name.ilike(f"%{query}%"))

    items = q.order_by(desc(AdAdGroup.updated_at)).limit(limit).offset(offset).all()
    return items

@router.get("/connections/{connection_id}/ads", response_model=list[AdAdOut])
def list_catalog_ads(
    connection_id: int,
    ad_group_external_id: str | None = None,
    query: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    _require_read(membership.role)
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение не найдено")

    q = db.query(AdAd).filter(AdAd.connection_id == connection_id)
    if ad_group_external_id:
        q = q.filter(AdAd.ad_group_external_id == ad_group_external_id)
    if query:
        q = q.filter(AdAd.name.ilike(f"%{query}%"))

    items = q.order_by(desc(AdAd.updated_at)).limit(limit).offset(offset).all()
    return items

# --- UTM Settings API ---

@router.get("/settings/utm", response_model=UtmSettingsOut)
def get_utm_settings(
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    _require_read(membership.role)
    settings = db.query(OrgUtmSettings).filter(OrgUtmSettings.organization_id == org.id).first()
    if not settings:
        # Return defaults if not set
        return UtmSettingsOut(
            organization_id=org.id,
            utm_source="{platform}",
            utm_medium="cpc",
            utm_campaign_tpl="{campaign_id}",
            utm_content_tpl="{ad_id}",
            utm_term_tpl=None
        )
    return settings

@router.put("/settings/utm", response_model=UtmSettingsOut)
def update_utm_settings(
    item: UtmSettingsUpdate,
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    _require_write(membership.role)
    settings = db.query(OrgUtmSettings).filter(OrgUtmSettings.organization_id == org.id).first()
    if not settings:
        settings = OrgUtmSettings(organization_id=org.id)
        db.add(settings)

    if item.utm_source is not None: settings.utm_source = item.utm_source
    if item.utm_medium is not None: settings.utm_medium = item.utm_medium
    if item.utm_campaign_tpl is not None: settings.utm_campaign_tpl = item.utm_campaign_tpl
    if item.utm_content_tpl is not None: settings.utm_content_tpl = item.utm_content_tpl
    if item.utm_term_tpl is not None: settings.utm_term_tpl = item.utm_term_tpl

    db.commit()
    db.refresh(settings)
    return settings

@router.post("/utm/build", response_model=UtmBuildResponse)
def build_utm_link(
    item: UtmBuildRequest,
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    _require_read(membership.role)
    ok, reason, normalized = normalize_and_validate_url(item.url)
    if not ok:
        raise HTTPException(status_code=422, detail=f"Invalid url: {reason}")

    settings = db.query(OrgUtmSettings).filter(OrgUtmSettings.organization_id == org.id).first()
    utm_params = build_utm_params(
        settings,
        None,
        platform=item.platform,
        campaign_id=item.campaign_external_id,
        ad_group_id=item.ad_group_external_id,
        ad_id=item.ad_external_id,
    )
    final_url = apply_utm(normalized, utm_params)
    return {"final_url": final_url}


@router.get("/utm/report", response_model=UtmReportResponse)
def utm_report(
    group_by: str = Query("campaign", regex="^(source|medium|campaign|content|term|source_campaign|source_medium_campaign|all)$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    utm_source: str | None = Query(None),
    utm_medium: str | None = Query(None),
    utm_campaign: str | None = Query(None),
    utm_content: str | None = Query(None),
    utm_term: str | None = Query(None),
    plan_id: int | None = Query(None),
    connection_id: int | None = Query(None),
    include_unlinked: bool = Query(False),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    _require_read(membership.role)
    if date_to is None:
        date_to = datetime.utcnow().date()
    if date_from is None:
        date_from = date_to - timedelta(days=30)
    if plan_id:
        include_unlinked = False

    start_dt = datetime.combine(date_from, time.min)
    end_dt = datetime.combine(date_to, time.max)

    lead_count = func.sum(
        case((ConversionEvent.event_type == ConversionEventType.lead, 1), else_=0)
    ).label("leads")
    purchase_count = func.sum(
        case((ConversionEvent.event_type == ConversionEventType.purchase, 1), else_=0)
    ).label("purchases")
    revenue_sum = func.sum(
        case((ConversionEvent.event_type == ConversionEventType.purchase, ConversionEvent.value), else_=0)
    ).label("revenue")
    total_events = func.count(ConversionEvent.id).label("total")

    group_cols = []
    if group_by in {"source", "source_campaign", "source_medium_campaign", "all"}:
        group_cols.append(ConversionEvent.utm_source.label("utm_source"))
    if group_by in {"medium", "source_medium_campaign", "all"}:
        group_cols.append(ConversionEvent.utm_medium.label("utm_medium"))
    if group_by in {"campaign", "source_campaign", "source_medium_campaign", "all"}:
        group_cols.append(ConversionEvent.utm_campaign.label("utm_campaign"))
    if group_by in {"content", "all"}:
        group_cols.append(ConversionEvent.utm_content.label("utm_content"))
    if group_by in {"term", "all"}:
        group_cols.append(ConversionEvent.utm_term.label("utm_term"))

    base_query = (
        db.query(ConversionEvent)
        .outerjoin(CampaignPlan, CampaignPlan.id == ConversionEvent.plan_id)
        .filter(ConversionEvent.occurred_at >= start_dt)
        .filter(ConversionEvent.occurred_at <= end_dt)
    )

    unlinked_condition = None
    if include_unlinked:
        unlinked_exists = exists().where(
            and_(
                AdCampaign.organization_id == org.id,
                AdCampaign.external_id == ConversionEvent.utm_campaign,
                cast(AdCampaign.platform, String) == ConversionEvent.utm_source,
            )
        )
        if connection_id:
            unlinked_exists = unlinked_exists.where(AdCampaign.connection_id == connection_id)
        unlinked_condition = and_(
            ConversionEvent.plan_id.is_(None),
            ConversionEvent.utm_campaign.isnot(None),
            unlinked_exists,
        )

    org_condition = CampaignPlan.organization_id == org.id
    if unlinked_condition is not None:
        org_condition = or_(org_condition, unlinked_condition)
    base_query = base_query.filter(org_condition)

    if plan_id:
        base_query = base_query.filter(ConversionEvent.plan_id == plan_id)
    if connection_id:
        if unlinked_condition is None:
            base_query = base_query.filter(CampaignPlan.connection_id == connection_id)
        else:
            base_query = base_query.filter(or_(CampaignPlan.connection_id == connection_id, unlinked_condition))
    if utm_source:
        base_query = base_query.filter(ConversionEvent.utm_source == utm_source)
    if utm_medium:
        base_query = base_query.filter(ConversionEvent.utm_medium == utm_medium)
    if utm_campaign:
        base_query = base_query.filter(ConversionEvent.utm_campaign == utm_campaign)
    if utm_content:
        base_query = base_query.filter(ConversionEvent.utm_content == utm_content)
    if utm_term:
        base_query = base_query.filter(ConversionEvent.utm_term == utm_term)

    totals_row = (
        base_query
        .with_entities(lead_count, purchase_count, revenue_sum, total_events)
        .first()
    )
    totals = UtmReportTotals(
        leads=int(totals_row.leads or 0) if totals_row else 0,
        purchases=int(totals_row.purchases or 0) if totals_row else 0,
        revenue=int(totals_row.revenue or 0) if totals_row else 0,
        total=int(totals_row.total or 0) if totals_row else 0,
    )

    query = base_query.with_entities(*group_cols, lead_count, purchase_count, revenue_sum, total_events)
    if group_cols:
        query = query.group_by(*group_cols)

    rows = (
        query.order_by(total_events.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items: list[UtmReportItem] = []
    for row in rows:
        data = {
            "utm_source": None,
            "utm_medium": None,
            "utm_campaign": None,
            "utm_content": None,
            "utm_term": None,
            "leads": int(row.leads or 0),
            "purchases": int(row.purchases or 0),
            "revenue": int(row.revenue or 0),
            "total": int(row.total or 0),
        }
        mapping = row._mapping
        for key in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"):
            if key in mapping:
                data[key] = mapping[key]
        items.append(UtmReportItem(**data))

    return UtmReportResponse(
        date_from=date_from,
        date_to=date_to,
        group_by=group_by,
        totals=totals,
        items=items,
    )


@router.get("/settings/utm/rules", response_model=list[UtmRuleOut])
def list_utm_rules(
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    _require_read(membership.role)
    return (
        db.query(OrgUtmRule)
        .filter(OrgUtmRule.organization_id == org.id)
        .order_by(OrgUtmRule.id.asc())
        .all()
    )


@router.post("/settings/utm/rules", response_model=UtmRuleOut)
def create_utm_rule(
    item: UtmRuleCreate,
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_write(membership.role)
    rule = OrgUtmRule(
        organization_id=org.id,
        is_enabled=item.is_enabled if item.is_enabled is not None else True,
        match_platform=item.match_platform,
        match_connection_id=item.match_connection_id,
        match_campaign_contains=item.match_campaign_contains,
        match_ad_group_contains=item.match_ad_group_contains,
        match_ad_contains=item.match_ad_contains,
        template_json=item.template_json or {},
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    log_org_event(
        db,
        organization_id=org.id,
        actor_user_id=user.id,
        action="utm_rule_changed",
        subject_type="utm_rule",
        subject_id=rule.id,
        meta={"changed_fields": ["created"]},
    )
    return rule


@router.patch("/settings/utm/rules/{rule_id}", response_model=UtmRuleOut)
def update_utm_rule(
    rule_id: int,
    item: UtmRuleUpdate,
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_write(membership.role)
    rule = (
        db.query(OrgUtmRule)
        .filter(OrgUtmRule.id == rule_id, OrgUtmRule.organization_id == org.id)
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")

    changed: list[str] = []
    for field in [
        "is_enabled",
        "match_platform",
        "match_connection_id",
        "match_campaign_contains",
        "match_ad_group_contains",
        "match_ad_contains",
        "template_json",
    ]:
        value = getattr(item, field)
        if value is not None:
            setattr(rule, field, value)
            changed.append(field)

    db.commit()
    db.refresh(rule)
    if changed:
        log_org_event(
            db,
            organization_id=org.id,
            actor_user_id=user.id,
            action="utm_rule_changed",
            subject_type="utm_rule",
            subject_id=rule.id,
            meta={"changed_fields": changed},
        )
    return rule


@router.post("/connections/{connection_id}/utm/reconcile")
def reconcile_connection_utm(
    connection_id: int,
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_write(membership.role)
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение не найдено")

    log_org_event(
        db,
        organization_id=org.id,
        actor_user_id=user.id,
        action="utm_reconcile_started",
        subject_type="connection",
        subject_id=conn.id,
        meta={},
    )
    counts = reconcile_ads_utm_for_connection(db, conn)
    log_org_event(
        db,
        organization_id=org.id,
        actor_user_id=user.id,
        action="utm_reconcile_finished",
        subject_type="connection",
        subject_id=conn.id,
        meta={"counts": counts},
    )
    return {"status": "ok", "counts": counts}


@router.get("/connections/{connection_id}/utm/status", response_model=UtmStatusOut)
def get_connection_utm_status(
    connection_id: int,
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    _require_read(membership.role)
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение не найдено")
    return get_utm_status_for_connection(db, connection_id)
