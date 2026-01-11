from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_org
from app.db.models import Organization, Connection, AdCampaign, AdAdGroup, AdAd, OrgUtmSettings
from app.db.session import get_db
from app.api.schemas import (
    AdCampaignOut, AdAdGroupOut, AdAdOut,
    UtmSettingsOut, UtmSettingsUpdate, UtmBuildRequest, UtmBuildResponse
)
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

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
            utm_term_tpl=None
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
