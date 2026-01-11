import pytest
from datetime import date
from app.db.models import ChangePlan, ChangePlanItem, AdCampaign, AdAd, OrgUtmSettings
from app.services.change_plans_service import create_plan, add_item, set_plan_status, execute_plan
from app.services.ad_catalog_service import refresh_catalog_for_connection

def test_change_plans_flow(session, org_a, user_a, connection_yandex, metric_snapshot_factory):
    # Setup catalog
    metric_snapshot_factory(
        connection=connection_yandex,
        campaign_external_id="c_plan",
        ad_group_external_id="g_plan",
        ad_external_id="a_plan"
    )
    refresh_catalog_for_connection(session, connection_yandex.id)

    camp = session.query(AdCampaign).filter_by(external_id="c_plan").first()
    ad = session.query(AdAd).filter_by(external_id="a_plan").first()

    # 1. Create Plan
    plan = create_plan(session, org_a.id, user_a.id, connection_yandex.id, "Test Plan")
    assert plan.status == "draft"

    # 2. Add Items
    item1 = add_item(session, org_a.id, plan.id, "campaign", camp.id, "pause", {})
    item2 = add_item(session, org_a.id, plan.id, "ad", ad.id, "update_url", {"url": "https://new.url"})

    assert item1.status == "pending"

    # 3. Mark Ready
    set_plan_status(session, org_a.id, plan.id, "ready")
    assert plan.status == "ready"

    # 4. Apply (Mock)
    # We call execute_plan which calls celery task. In tests (if celery eager or we call task directly), it runs.
    # Let's call task directly to ensure execution in test session context?
    # Or rely on celery_app.conf.task_always_eager = True if set.
    # Assuming standard test setup might not have eager.
    # Let's import task and run it synchronously for test.
    from app.workers.change_plan_tasks import apply_change_plan
    apply_change_plan(plan.id)

    session.refresh(plan)
    session.refresh(item1)
    session.refresh(item2)
    session.refresh(camp)
    session.refresh(ad)

    assert plan.status == "applied"
    assert item1.status == "applied"
    assert camp.desired_status == "paused"
    assert ad.desired_url == "https://new.url"

def test_change_plans_utm(session, org_a, user_a, connection_yandex, metric_snapshot_factory):
    # Setup catalog
    metric_snapshot_factory(
        connection=connection_yandex,
        campaign_external_id="c_utm",
        ad_group_external_id="g_utm",
        ad_external_id="a_utm"
    )
    refresh_catalog_for_connection(session, connection_yandex.id)
    ad = session.query(AdAd).filter_by(external_id="a_utm").first()

    # Setup UTM settings
    settings = OrgUtmSettings(organization_id=org_a.id, utm_source="test_src")
    session.add(settings)
    session.commit()

    # Plan
    plan = create_plan(session, org_a.id, user_a.id, connection_yandex.id, "UTM Plan")
    add_item(session, org_a.id, plan.id, "ad", ad.id, "apply_utm", {"base_url": "https://site.com"})
    set_plan_status(session, org_a.id, plan.id, "ready")

    from app.workers.change_plan_tasks import apply_change_plan
    apply_change_plan(plan.id)

    session.refresh(ad)
    assert "utm_source=test_src" in ad.desired_url
    assert "https://site.com" in ad.desired_url

def test_change_plans_scoping(session, org_b, user_b, connection_yandex):
    # connection_yandex is in org_a
    # User B tries to create plan for connection A -> should fail
    try:
        create_plan(session, org_b.id, user_b.id, connection_yandex.id, "Hack Plan")
        assert False, "Should raise error"
    except ValueError as e:
        assert "Подключение не найдено" in str(e)
