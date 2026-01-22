import traceback
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db import session as db_session
from app.db.models import ChangePlan, ChangePlanItem, AdCampaign, AdAdGroup, AdAd, OrgUtmSettings, OrgUtmRule
from app.services.audit import log_org_event
from app.services.utm_service import apply_utm, build_utm_params, normalize_and_validate_url, pick_matching_rule
from app.workers.celery_app import celery_app
from app.core.context import set_correlation_id

@celery_app.task(bind=True, max_retries=3)
def apply_change_plan(self, plan_id: int, correlation_id: str | None = None):
    if correlation_id:
        set_correlation_id(correlation_id)

    db = db_session.get_session()
    try:
        plan = db.query(ChangePlan).get(plan_id)
        if not plan:
            return "Plan not found"

        if plan.status == "applied":
            return "Already applied"

        items = db.query(ChangePlanItem).filter(ChangePlanItem.plan_id == plan.id).all()

        # Load UTM settings and rules for apply_utm
        utm_settings = db.query(OrgUtmSettings).filter(OrgUtmSettings.organization_id == plan.organization_id).first()
        utm_rules = (
            db.query(OrgUtmRule)
            .filter(OrgUtmRule.organization_id == plan.organization_id)
            .order_by(OrgUtmRule.id.asc())
            .all()
        )

        def _resolve_base_url(ad: AdAd, base_url_override: str | None) -> str | None:
            return base_url_override or ad.target_url or ad.desired_url

        def _load_ad_context(ad: AdAd) -> tuple[AdAdGroup | None, AdCampaign | None]:
            group = (
                db.query(AdAdGroup)
                .filter(
                    AdAdGroup.connection_id == ad.connection_id,
                    AdAdGroup.external_id == ad.ad_group_external_id,
                )
                .first()
            )
            campaign = (
                db.query(AdCampaign)
                .filter(
                    AdCampaign.connection_id == ad.connection_id,
                    AdCampaign.external_id == ad.campaign_external_id,
                )
                .first()
            )
            return group, campaign

        def _build_final_url(
            ad: AdAd,
            group: AdAdGroup | None,
            campaign: AdCampaign | None,
            base_url_override: str | None,
        ) -> str:
            base_url = _resolve_base_url(ad, base_url_override)
            ok, reason, normalized = normalize_and_validate_url(base_url)
            if not ok:
                raise ValueError(reason or "invalid_url")

            rule = pick_matching_rule(
                utm_rules,
                platform=ad.platform,
                connection_id=ad.connection_id,
                campaign_name=campaign.name if campaign else None,
                ad_group_name=group.name if group else None,
                ad_name=ad.name,
            )
            params = build_utm_params(
                utm_settings,
                rule,
                platform=ad.platform,
                campaign_id=ad.campaign_external_id,
                ad_group_id=ad.ad_group_external_id,
                ad_id=ad.external_id,
            )
            return apply_utm(normalized, params)

        success_count = 0
        fail_count = 0

        for item in items:
            try:
                params = item.params_json or {}
                if item.subject_type == "campaign":
                    camp = db.query(AdCampaign).get(item.subject_id)
                    if not camp:
                        raise ValueError("Campaign not found")

                    if item.action_type == "pause":
                        camp.desired_status = "paused"
                    elif item.action_type == "resume":
                        camp.desired_status = "active"
                    elif item.action_type == "set_daily_budget":
                        camp.desired_daily_budget = params.get("amount")
                    elif item.action_type == "apply_utm":
                        base_url_override = params.get("base_url")
                        ads = (
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
                            .filter(
                                AdAd.connection_id == camp.connection_id,
                                AdAd.campaign_external_id == camp.external_id,
                            )
                            .all()
                        )
                        if not ads:
                            raise ValueError("No ads found for campaign")

                        updated = 0
                        for ad, group, campaign in ads:
                            try:
                                final_url = _build_final_url(ad, group, campaign or camp, base_url_override)
                            except ValueError:
                                continue
                            ad.desired_url = final_url
                            updated += 1

                        if updated == 0:
                            raise ValueError("No ads with valid url")
                    else:
                        raise ValueError("Unsupported campaign action")

                elif item.subject_type == "ad":
                    ad = db.query(AdAd).get(item.subject_id)
                    if not ad:
                        raise ValueError("Ad not found")

                    if item.action_type == "update_url":
                        url = params.get("url")
                        if not url:
                            raise ValueError("Missing url")
                        ad.desired_url = url
                    elif item.action_type == "apply_utm":
                        base_url_override = params.get("base_url")
                        group, campaign = _load_ad_context(ad)
                        final = _build_final_url(ad, group, campaign, base_url_override)
                        ad.desired_url = final
                    else:
                        raise ValueError("Unsupported ad action")
                else:
                    raise ValueError("Unsupported subject type")

                item.status = "applied"
                success_count += 1
            except Exception as e:
                item.status = "failed"
                item.error = str(e)
                fail_count += 1

        plan.status = "applied" if fail_count == 0 else "failed" # Or partially applied?
        # Let's say applied if at least one success? Or strict?
        # Strict: failed if any failed.
        if fail_count > 0:
            plan.status = "failed"
            plan.error = f"{fail_count} items failed"

        plan.applied_at = datetime.now(timezone.utc)

        log_org_event(
            db,
            organization_id=plan.organization_id,
            actor_user_id=plan.created_by_user_id,
            action=f"change_plan_{plan.status}",
            subject_type="change_plan",
            subject_id=plan.id,
            meta={"success": success_count, "failed": fail_count}
        )

        db.commit()

    except Exception as e:
        db.rollback()
        # Log error
        print(f"Plan execution failed: {e}")
    finally:
        if not db_session.is_test_session(db):
            db.close()
