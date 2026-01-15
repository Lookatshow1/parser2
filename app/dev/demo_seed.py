from __future__ import annotations

from datetime import date, datetime, timedelta, timezone, time
from typing import Iterable

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import (
    User,
    Organization,
    Membership,
    MembershipRole,
    Connection,
    ConnectionStatus,
    Platform,
    SyncRun,
    SyncRunStatus,
    SyncRunType,
    JobRun,
    JobStatus,
    MetricSnapshot,
    Experiment,
    ExperimentStatus,
    BuilderCampaign,
    BuilderAdGroup,
    BuilderAd,
    ChangePlan,
    ChangePlanItem,
    AdCampaign,
    AdAd,
    OrgProfile
)
from app.security.credentials_crypto import maybe_encrypt
from app.services.auth_service import get_password_hash
from app.services.ad_catalog_service import refresh_catalog_for_connection


DEMO_MEMBER_EMAIL = "demo.member@example.com"
DEMO_VIEWER_EMAIL = "demo.viewer@example.com"
DEMO_MEMBER_PASSWORD = "demo12345"


def _parse_connection_names(value: str) -> list[str]:
    names = [item.strip() for item in value.split(",") if item.strip()]
    return names or ["Яндекс.Директ: Демо 1", "Яндекс.Директ: Демо 2"]


def _ensure_user(session: Session, email: str, password: str, force_password: bool) -> User:
    user = session.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            is_active=True,
        )
        session.add(user)
        session.flush()
        return user
    if force_password:
        user.password_hash = get_password_hash(password)
    user.is_active = True
    return user


def _ensure_org(session: Session, name: str) -> Organization:
    org = session.query(Organization).filter(Organization.name == name).first()
    if org is None:
        org = Organization(name=name)
        session.add(org)
        session.flush()
    return org


def _ensure_org_profile(session: Session, org: Organization) -> OrgProfile:
    profile = session.query(OrgProfile).filter(OrgProfile.organization_id == org.id).first()
    if profile is None:
        profile = OrgProfile(
            organization_id=org.id,
            legal_type="ООО",
            legal_name="Демо-организация",
            inn="7700000000",
            kpp="770001001",
            ogrn="1027700000000",
            legal_address="Москва, ул. Демонстрационная, 1",
            email_for_docs="demo@example.com",
            phone="+7 999 000-00-00",
            timezone="Europe/Moscow",
            currency="RUB",
        )
        session.add(profile)
        session.flush()
    return profile


def _ensure_membership(session: Session, user: User, org: Organization, role: str) -> Membership:
    membership = (
        session.query(Membership)
        .filter(Membership.user_id == user.id, Membership.organization_id == org.id)
        .first()
    )
    if membership is None:
        membership = Membership(user_id=user.id, organization_id=org.id, role=role)
        session.add(membership)
        session.flush()
    else:
        membership.role = role
    return membership


def _ensure_connection(
    session: Session,
    org: Organization,
    name: str,
    credentials: dict,
) -> Connection:
    connection = (
        session.query(Connection)
        .filter(Connection.organization_id == org.id, Connection.platform == Platform.yandex, Connection.name == name)
        .first()
    )
    encrypted = maybe_encrypt(credentials)
    if connection is None:
        connection = Connection(
            organization_id=org.id,
            platform=Platform.yandex,
            name=name,
            credentials_json=encrypted,
            status=ConnectionStatus.active,
        )
        session.add(connection)
        session.flush()
    else:
        connection.credentials_json = encrypted
        connection.status = ConnectionStatus.active
    return connection


def _metric_seed(connection_id: int, day: date, campaign_idx: int) -> int:
    base = int(day.strftime("%Y%m%d"))
    return base + connection_id * 37 + campaign_idx * 19


def _metric_values(connection_id: int, day: date, campaign_idx: int) -> dict:
    seed = _metric_seed(connection_id, day, campaign_idx)
    impressions = 1200 + seed % 800
    clicks = max(20, impressions // 22)
    spend = 250 + seed % 180
    leads = max(1, clicks // 7)
    purchases = max(1, clicks // 15)
    revenue = spend * 3
    return {
        "impressions": int(impressions),
        "clicks": int(clicks),
        "spend": int(spend),
        "leads": int(leads),
        "purchases": int(purchases),
        "revenue": int(revenue),
    }


def _ensure_snapshot(
    session: Session,
    org: Organization,
    connection: Connection,
    day: date,
    campaign_external_id: str,
    metrics: dict,
) -> MetricSnapshot:
    existing = (
        session.query(MetricSnapshot)
        .filter(
            MetricSnapshot.organization_id == org.id,
            MetricSnapshot.connection_id == connection.id,
            MetricSnapshot.platform == Platform.yandex,
            MetricSnapshot.date == day,
            MetricSnapshot.level == "campaign",
            MetricSnapshot.campaign_external_id == campaign_external_id,
        )
        .first()
    )
    if existing is None:
        existing = MetricSnapshot(
            organization_id=org.id,
            connection_id=connection.id,
            platform=Platform.yandex,
            date=day,
            level="campaign",
            campaign_external_id=campaign_external_id,
            ad_group_external_id=None,
            ad_external_id=None,
            impressions=metrics["impressions"],
            clicks=metrics["clicks"],
            spend=metrics["spend"],
            leads=metrics["leads"],
            purchases=metrics["purchases"],
            revenue=metrics["revenue"],
        )
        session.add(existing)
    else:
        existing.impressions = metrics["impressions"]
        existing.clicks = metrics["clicks"]
        existing.spend = metrics["spend"]
        existing.leads = metrics["leads"]
        existing.purchases = metrics["purchases"]
        existing.revenue = metrics["revenue"]
    return existing


def _find_demo_sync_run(runs: Iterable[SyncRun], date_from: date, date_to: date) -> SyncRun | None:
    target_from = date_from.isoformat()
    target_to = date_to.isoformat()
    for run in runs:
        params = run.params_json or {}
        if not params.get("demo_seed"):
            continue
        if params.get("date_from") == target_from and params.get("date_to") == target_to:
            return run
    return None


def _ensure_sync_run(
    session: Session,
    org: Organization,
    connection: Connection,
    date_from: date,
    date_to: date,
    status: SyncRunStatus,
    result_json: dict | None,
    error_text: str | None,
) -> SyncRun:
    existing_runs = (
        session.query(SyncRun)
        .filter(SyncRun.organization_id == org.id, SyncRun.connection_id == connection.id)
        .all()
    )
    run = _find_demo_sync_run(existing_runs, date_from, date_to)
    created_at = datetime.combine(date_to, time(12, 0), tzinfo=timezone.utc)
    started_at = created_at - timedelta(minutes=5)
    finished_at = created_at
    params_json = {
        "demo_seed": True,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }
    if run is None:
        run = SyncRun(
            organization_id=org.id,
            connection_id=connection.id,
            platform=Platform.yandex,
            run_type=SyncRunType.metrics,
            status=status,
            params_json=params_json,
            result_json=result_json,
            error_text=error_text,
            started_at=started_at,
            finished_at=finished_at,
            created_at=created_at,
        )
        session.add(run)
        session.flush()
    else:
        run.platform = Platform.yandex
        run.run_type = SyncRunType.metrics
        run.status = status
        run.params_json = params_json
        run.result_json = result_json
        run.error_text = error_text
        run.started_at = started_at
        run.finished_at = finished_at
    return run


def _ensure_job_run(session: Session, org: Organization, connection: Connection, run: SyncRun) -> JobRun:
    existing_jobs = (
        session.query(JobRun)
        .filter(JobRun.organization_id == org.id, JobRun.connection_id == connection.id)
        .all()
    )
    for job in existing_jobs:
        context = job.context_json or {}
        if context.get("demo_seed") and context.get("sync_run_id") == run.id:
            job.status = JobStatus.success if run.status == SyncRunStatus.success else JobStatus.failed
            job.result_json = run.result_json
            job.error_text = run.error_text
            job.started_at = run.started_at
            job.finished_at = run.finished_at
            return job

    status = JobStatus.success if run.status == SyncRunStatus.success else JobStatus.failed
    job = JobRun(
        organization_id=org.id,
        connection_id=connection.id,
        job_type="sync",
        status=status,
        context_json={"demo_seed": True, "sync_run_id": run.id},
        result_json=run.result_json,
        error_text=run.error_text,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )
    session.add(job)
    return job

def _ensure_builder_data(session: Session, org: Organization):
    # Ensure experiment
    experiment = session.query(Experiment).filter(
        Experiment.organization_id == org.id,
        Experiment.status == ExperimentStatus.draft
    ).first()

    if not experiment:
        experiment = Experiment(
            organization_id=org.id,
            total_budget=50000,
            platforms=["yandex"],
            status=ExperimentStatus.draft
        )
        session.add(experiment)
        session.flush()

    # Ensure campaign
    campaign = session.query(BuilderCampaign).filter(
        BuilderCampaign.experiment_id == experiment.id,
        BuilderCampaign.name == "Демо Кампания"
    ).first()

    if not campaign:
        campaign = BuilderCampaign(
            organization_id=org.id,
            experiment_id=experiment.id,
            platform=Platform.yandex,
            name="Демо Кампания",
            status="draft"
        )
        session.add(campaign)
        session.flush()

    # Ensure group
    group = session.query(BuilderAdGroup).filter(
        BuilderAdGroup.campaign_id == campaign.id,
        BuilderAdGroup.name == "Группа 1"
    ).first()

    if not group:
        group = BuilderAdGroup(
            organization_id=org.id,
            campaign_id=campaign.id,
            name="Группа 1",
            status="draft"
        )
        session.add(group)
        session.flush()

    # Ensure ad
    ad = session.query(BuilderAd).filter(
        BuilderAd.ad_group_id == group.id,
        BuilderAd.name == "Объявление 1"
    ).first()

    if not ad:
        from app.utils.utm import build_utm_url
        base_url = "https://example.com/landing"
        utm_json = {
            "utm_source": "yandex",
            "utm_medium": "cpc",
            "utm_campaign": "demo_campaign",
            "utm_content": "banner_1",
            "utm_term": "buy_now"
        }
        final_url = build_utm_url(base_url, utm_json)

        ad = BuilderAd(
            organization_id=org.id,
            ad_group_id=group.id,
            name="Объявление 1",
            title="Лучшее предложение",
            text="Покупайте наших слонов, они лучшие на рынке!",
            base_url=base_url,
            utm_json=utm_json,
            final_url=final_url,
            status="draft"
        )
        session.add(ad)
        session.flush()

def _ensure_change_plans(session: Session, org: Organization, user: User, connection: Connection):
    # Ensure catalog is populated
    refresh_catalog_for_connection(session, connection.id)

    # Find a campaign
    camp = session.query(AdCampaign).filter(AdCampaign.connection_id == connection.id).first()
    if not camp:
        return

    # 1. Applied Plan
    plan_applied = session.query(ChangePlan).filter(
        ChangePlan.organization_id == org.id,
        ChangePlan.title == "Демо: Остановка кампании"
    ).first()

    if not plan_applied:
        plan_applied = ChangePlan(
            organization_id=org.id,
            connection_id=connection.id,
            title="Демо: Остановка кампании",
            status="applied",
            created_by_user_id=user.id,
            applied_at=datetime.now(timezone.utc)
        )
        session.add(plan_applied)
        session.flush()

        item = ChangePlanItem(
            plan_id=plan_applied.id,
            subject_type="campaign",
            subject_id=camp.id,
            action_type="pause",
            params_json={},
            status="applied"
        )
        session.add(item)

        # Update catalog state
        camp.desired_status = "paused"

    # 2. Draft Plan
    plan_draft = session.query(ChangePlan).filter(
        ChangePlan.organization_id == org.id,
        ChangePlan.title == "Демо: Увеличение бюджета"
    ).first()

    if not plan_draft:
        plan_draft = ChangePlan(
            organization_id=org.id,
            connection_id=connection.id,
            title="Демо: Увеличение бюджета",
            status="draft",
            created_by_user_id=user.id
        )
        session.add(plan_draft)
        session.flush()

        item = ChangePlanItem(
            plan_id=plan_draft.id,
            subject_type="campaign",
            subject_id=camp.id,
            action_type="set_daily_budget",
            params_json={"amount": 5000},
            status="pending"
        )
        session.add(item)


def seed_demo(session: Session) -> dict:
    settings = get_settings()
    demo_email = settings.demo_email.lower()
    demo_password = settings.demo_password
    demo_org_name = settings.demo_org_name
    demo_connections = _parse_connection_names(settings.demo_connections)

    demo_user = _ensure_user(session, demo_email, demo_password, settings.demo_force_password)
    demo_member = _ensure_user(session, DEMO_MEMBER_EMAIL, DEMO_MEMBER_PASSWORD, False)
    demo_viewer = _ensure_user(session, DEMO_VIEWER_EMAIL, DEMO_MEMBER_PASSWORD, False)

    org = _ensure_org(session, demo_org_name)
    _ensure_org_profile(session, org)

    _ensure_membership(session, demo_user, org, MembershipRole.owner.value)
    _ensure_membership(session, demo_member, org, MembershipRole.member.value)
    _ensure_membership(session, demo_viewer, org, MembershipRole.viewer.value)

    demo_user.active_organization_id = org.id

    connections = [
        _ensure_connection(session, org, name, {"mock": True}) for name in demo_connections
    ]

    today = date.today()
    period_from = today - timedelta(days=13)
    period_to = today

    # Snapshots
    for connection in connections:
        for idx, campaign_id in enumerate(["demo_campaign_1", "demo_campaign_2"], start=1):
            for offset in range((period_to - period_from).days + 1):
                current_day = period_from + timedelta(days=offset)
                metrics = _metric_values(connection.id, current_day, idx)
                _ensure_snapshot(
                    session,
                    org,
                    connection,
                    current_day,
                    f"{campaign_id}_{connection.id}",
                    metrics,
                )

    # Sync runs + job runs
    run_specs = [
        (period_from, period_from + timedelta(days=4), SyncRunStatus.success, None),
        (period_from + timedelta(days=5), period_from + timedelta(days=9), SyncRunStatus.success, None),
        (period_from + timedelta(days=10), period_to, SyncRunStatus.success, None),
        (period_from + timedelta(days=3), period_from + timedelta(days=3), SyncRunStatus.failed, "Demo sync failed"),
    ]

    for connection in connections:
        for date_from, date_to, status, error in run_specs:
            days = (date_to - date_from).days + 1
            records = days * 2
            result = None
            if status == SyncRunStatus.success:
                result = {
                    "inserted": records,
                    "updated": 0,
                    "unchanged": 0,
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                    "demo_seed": True,
                }
            run = _ensure_sync_run(session, org, connection, date_from, date_to, status, result, error)
            _ensure_job_run(session, org, connection, run)

        # Change plans
        _ensure_change_plans(session, org, demo_user, connection)

    # Builder data
    _ensure_builder_data(session, org)

    session.commit()

    return {
        "demo_user_email": demo_email,
        "demo_password": demo_password,
        "org_id": org.id,
        "connection_ids": [conn.id for conn in connections],
        "period_from": period_from.isoformat(),
        "period_to": period_to.isoformat(),
    }
