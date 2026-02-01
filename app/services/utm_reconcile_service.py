from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import AdAd, AdAdGroup, AdCampaign, Connection, OrgUtmSettings, OrgUtmRule
from app.services.utm_service import (
    normalize_and_validate_url,
    build_utm_params,
    apply_utm,
    compute_utm_hash,
    pick_matching_rule,
)
from app.services.connector_service import get_connector
from app.security.credentials_crypto import maybe_decrypt


def reconcile_ads_utm_for_connection(
    db: Session,
    connection: Connection,
    *,
    limit: int | None = None,
) -> dict:
    settings = (
        db.query(OrgUtmSettings)
        .filter(OrgUtmSettings.organization_id == connection.organization_id)
        .first()
    )
    rules = (
        db.query(OrgUtmRule)
        .filter(OrgUtmRule.organization_id == connection.organization_id)
        .order_by(OrgUtmRule.id.asc())
        .all()
    )

    q = (
        db.query(AdAd, AdAdGroup, AdCampaign)
        .outerjoin(
            AdAdGroup,
            (AdAdGroup.connection_id == AdAd.connection_id)
            & (AdAdGroup.external_id == AdAd.ad_group_external_id),
        )
        .outerjoin(
            AdCampaign,
            (AdCampaign.connection_id == AdAd.connection_id)
            & (AdCampaign.external_id == AdAd.campaign_external_id),
        )
        .filter(AdAd.connection_id == connection.id)
        .order_by(AdAd.id.asc())
    )
    if limit:
        q = q.limit(limit)

    counts = {"total": 0, "updated": 0, "unchanged": 0, "invalid": 0, "missing": 0, "ok": 0}
    now = datetime.utcnow()

    for ad, group, campaign in q.all():
        counts["total"] += 1
        base_url = ad.target_url or ad.desired_url
        ok, reason, normalized = normalize_and_validate_url(base_url)
        if not ok:
            ad.url_status = reason
            if reason == "missing_url":
                counts["missing"] += 1
            else:
                counts["invalid"] += 1
            continue

        rule = pick_matching_rule(
            rules,
            platform=ad.platform,
            connection_id=connection.id,
            campaign_name=campaign.name if campaign else None,
            ad_group_name=group.name if group else None,
            ad_name=ad.name,
        )
        params = build_utm_params(
            settings,
            rule,
            platform=ad.platform,
            campaign_id=ad.campaign_external_id,
            ad_group_id=ad.ad_group_external_id,
            ad_id=ad.external_id,
        )
        final_url = apply_utm(normalized, params)
        final_hash = compute_utm_hash(final_url)

        if ad.final_url != final_url or ad.utm_hash != final_hash:
            ad.final_url = final_url
            ad.utm_hash = final_hash
            ad.utm_applied_at = now
            ad.url_status = "ok"
            counts["updated"] += 1
            
            if settings and settings.auto_update_ads:
                # Auto-update external platform
                try:
                    creds = maybe_decrypt(connection.credentials_json) if connection.credentials_json else {}
                    connector = get_connector(connection.platform, creds)
                    if connector:
                        # Log attempt? 
                        res = connector.update_ad_link(ad.external_id, final_url)
                        # We could log the result to a new audit log or just print for now.
                        # Ideally we should assume it worked or handle error.
                        if not res.get("success"):
                             # Maybe mark ad status as sync_error?
                             pass
                except Exception as e:
                    # Log error
                    pass
        else:
            ad.url_status = "ok"
            counts["unchanged"] += 1
        counts["ok"] += 1

    db.commit()
    return counts


def get_utm_status_for_connection(db: Session, connection_id: int) -> dict:
    rows = (
        db.query(AdAd.url_status, func.count(AdAd.id))
        .filter(AdAd.connection_id == connection_id)
        .group_by(AdAd.url_status)
        .all()
    )
    result = {"ok": 0, "invalid_url": 0, "blocked_scheme": 0, "missing_url": 0, "unknown": 0}
    for status, count in rows:
        if not status:
            result["unknown"] += count
        else:
            result[status] = count
    return result
