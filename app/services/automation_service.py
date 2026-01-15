from __future__ import annotations

from datetime import datetime, timedelta, date

from sqlalchemy.orm import Session

from app.db.models import (
    Organization,
    OrgAutomationSettings,
    OrgAutomationRun,
    OrgAutomationAction,
    OrgRecommendation,
)
from app.services.recommendations_service import compute_recommendations_for_org
from app.services.audit import log_org_event


def get_or_create_settings(db: Session, org_id: int) -> OrgAutomationSettings:
    settings = (
        db.query(OrgAutomationSettings)
        .filter(OrgAutomationSettings.organization_id == org_id)
        .first()
    )
    if not settings:
        settings = OrgAutomationSettings(organization_id=org_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def run_automation_for_org(
    db: Session,
    org: Organization,
    *,
    actor_user_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> OrgAutomationRun:
    running = (
        db.query(OrgAutomationRun)
        .filter(
            OrgAutomationRun.organization_id == org.id,
            OrgAutomationRun.status == "running",
        )
        .first()
    )
    if running:
        return running

    run = OrgAutomationRun(
        organization_id=org.id,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    log_org_event(
        db,
        organization_id=org.id,
        actor_user_id=actor_user_id,
        action="automation_run_started",
        subject_type="automation_run",
        subject_id=run.id,
        meta={},
    )

    if not date_to:
        date_to = date.today()
    if not date_from:
        date_from = date_to - timedelta(days=14)

    try:
        created, updated = compute_recommendations_for_org(db, org.id, date_from, date_to)
        recos = (
            db.query(OrgRecommendation)
            .filter(
                OrgRecommendation.organization_id == org.id,
                OrgRecommendation.valid_from <= date_to,
                OrgRecommendation.valid_to >= date_from,
            )
            .all()
        )

        created_actions = 0
        for rec in recos:
            exists = (
                db.query(OrgAutomationAction)
                .filter(
                    OrgAutomationAction.organization_id == org.id,
                    OrgAutomationAction.recommendation_id == rec.id,
                    OrgAutomationAction.status == "draft",
                )
                .first()
            )
            if exists:
                continue
            action = OrgAutomationAction(
                organization_id=org.id,
                run_id=run.id,
                recommendation_id=rec.id,
                action_type=rec.code,
                status="draft",
                title=rec.title,
                description=rec.description,
                payload_json={
                    "recommendation_code": rec.code,
                    "subject_type": rec.subject_type,
                    "subject_id": rec.subject_id,
                    "action": rec.action,
                    "meta": rec.meta_json or {},
                },
            )
            db.add(action)
            created_actions += 1

        run.status = "success"
        run.finished_at = datetime.utcnow()
        run.result_json = {
            "recommendations_created": created,
            "recommendations_updated": updated,
            "actions_created": created_actions,
            "window": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        }
        settings = get_or_create_settings(db, org.id)
        settings.last_run_at = datetime.utcnow()
        db.commit()

        log_org_event(
            db,
            organization_id=org.id,
            actor_user_id=actor_user_id,
            action="automation_run_finished",
            subject_type="automation_run",
            subject_id=run.id,
            meta=run.result_json,
        )
        return run
    except Exception as exc:
        run.status = "failed"
        run.finished_at = datetime.utcnow()
        run.error_text = "Ошибка автопилота"
        run.result_json = {"error": "automation_failed"}
        settings = get_or_create_settings(db, org.id)
        settings.last_run_at = datetime.utcnow()
        db.commit()
        log_org_event(
            db,
            organization_id=org.id,
            actor_user_id=actor_user_id,
            action="automation_run_failed",
            subject_type="automation_run",
            subject_id=run.id,
            meta={"error": "automation_failed"},
        )
        return run


def should_run(settings: OrgAutomationSettings, now: datetime) -> bool:
    if not settings.is_enabled:
        return False
    if not settings.last_run_at:
        return True
    delta = now - settings.last_run_at
    return delta.total_seconds() >= settings.run_interval_minutes * 60
