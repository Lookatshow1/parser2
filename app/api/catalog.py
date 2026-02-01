from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_org, get_current_user
from app.db.models import Organization, Connection, AdCampaign, AdAdGroup, AdAd, OrgUtmSettings, OrgUtmRule, User
from app.db.session import get_db
from app.api.schemas import (
    AdCampaignOut, AdAdGroupOut, AdAdOut,
    UtmSettingsOut, UtmSettingsUpdate, UtmBuildRequest, UtmBuildResponse,
    UtmRuleOut, UtmRuleCreate, UtmRuleUpdate, UtmStatusOut
)
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse
from app.services.utm_reconcile_service import reconcile_ads_utm_for_connection, get_utm_status_for_connection
from app.services.audit import log_org_event

router = APIRouter(tags=["catalog"])

# --- Catalog Read API ---

@router.get("/connections/{connection_id}/campaigns", response_model=list[AdCampaignOut])
def list_catalog_campaigns(
    connection_id: int,
    query: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
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
    db: Session = Depends(get_db)
):
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
    db: Session = Depends(get_db)
):
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
    db: Session = Depends(get_db)
):
    settings = db.query(OrgUtmSettings).filter(OrgUtmSettings.organization_id == org.id).first()
    if not settings:
        # Return defaults if not set
        return UtmSettingsOut(
            organization_id=org.id,
            utm_source="{platform}",
            utm_medium="cpc",
            utm_campaign_tpl="{campaign_id}",
            utm_content_tpl="{ad_id}",
            utm_content_tpl="{ad_id}",
            utm_term_tpl=None,
            auto_update_ads=False
        )
    return settings

@router.put("/settings/utm", response_model=UtmSettingsOut)
def update_utm_settings(
    item: UtmSettingsUpdate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    settings = db.query(OrgUtmSettings).filter(OrgUtmSettings.organization_id == org.id).first()
    if not settings:
        settings = OrgUtmSettings(organization_id=org.id)
        db.add(settings)

    if item.utm_source is not None: settings.utm_source = item.utm_source
    if item.utm_medium is not None: settings.utm_medium = item.utm_medium
    if item.utm_campaign_tpl is not None: settings.utm_campaign_tpl = item.utm_campaign_tpl
    if item.utm_content_tpl is not None: settings.utm_content_tpl = item.utm_content_tpl
    if item.utm_term_tpl is not None: settings.utm_term_tpl = item.utm_term_tpl
    if item.auto_update_ads is not None: settings.auto_update_ads = item.auto_update_ads

    db.commit()
    db.refresh(settings)
    return settings

@router.post("/utm/build", response_model=UtmBuildResponse)
def build_utm_link(
    item: UtmBuildRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    settings = db.query(OrgUtmSettings).filter(OrgUtmSettings.organization_id == org.id).first()
    # Defaults
    s_source = settings.utm_source if settings else "{platform}"
    s_medium = settings.utm_medium if settings else "cpc"
    s_campaign = settings.utm_campaign_tpl if settings else "{campaign_id}"
    s_content = settings.utm_content_tpl if settings else "{ad_id}"
    s_term = settings.utm_term_tpl if settings else None

    # Replacements
    def replace(tpl: str | None) -> str | None:
        if not tpl: return None
        res = tpl.replace("{platform}", item.platform.value if item.platform else "")
        res = res.replace("{campaign_id}", item.campaign_external_id or "")
        res = res.replace("{ad_group_id}", item.ad_group_external_id or "")
        res = res.replace("{ad_id}", item.ad_external_id or "")
        # If placeholder resulted in empty string and it was the only content, return None or empty?
        # Let's keep empty string if it was just a placeholder.
        return res

    utm_params = {
        "utm_source": replace(s_source),
        "utm_medium": replace(s_medium),
        "utm_campaign": replace(s_campaign),
        "utm_content": replace(s_content),
        "utm_term": replace(s_term),
    }

    # Filter empty
    utm_params = {k: v for k, v in utm_params.items() if v}

    # Build URL
    parsed = urlparse(item.url)
    existing_query = parse_qsl(parsed.query)

    # Merge: existing params take precedence? Usually UTMs are appended.
    # Let's append.
    final_query = existing_query + list(utm_params.items())
    encoded_query = urlencode(final_query)

    final_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        encoded_query,
        parsed.fragment
    ))

    return {"final_url": final_url}


@router.get("/settings/utm/rules", response_model=list[UtmRuleOut])
def list_utm_rules(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
    db: Session = Depends(get_db),
):
    conn = db.query(Connection).filter(Connection.id == connection_id, Connection.organization_id == org.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение не найдено")
    return get_utm_status_for_connection(db, connection_id)
