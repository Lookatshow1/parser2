from datetime import datetime, timezone
from uuid import uuid4

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

from app.db.models import CampaignPlan, Experiment, ExperimentStatus, Platform


def seed_plan(session, organization_id: int):
    plan = CampaignPlan(
        organization_id=organization_id,
        advertiser_id=1,
        name="Idempotency Plan",
        platform=Platform.yandex,
        internal_code="campaign-123",
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    experiment = Experiment(plan_id=plan.id, organization_id=organization_id, status=ExperimentStatus.draft)
    session.add(experiment)
    session.commit()
    return plan


def test_lead_event_idempotent(client, db_session, default_org_id):
    seed_plan(db_session, default_org_id)

    payload = {
        "event_id": str(uuid4()),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "landing_url": "https://example.com/landing",
        "utm_campaign": "campaign-123",
        "utm_source": "yandex",
        "contact": {"email": "lead@example.com"},
    }

    response_first = client.post("/api/events/lead", json=payload)
    response_second = client.post("/api/events/lead", json=payload)

    assert response_first.status_code == 200
    assert response_first.json()["idempotent"] is False
    assert response_second.status_code == 200
    assert response_second.json()["idempotent"] is True

    count = db_session.execute(text("SELECT COUNT(*) FROM conversion_events")).scalar_one()
    assert count == 1


def test_purchase_event_idempotent(client, db_session, default_org_id):
    seed_plan(db_session, default_org_id)

    payload = {
        "event_id": str(uuid4()),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "landing_url": "https://example.com/landing",
        "utm_campaign": "campaign-123",
        "utm_source": "vk",
        "value": 1500,
        "contact": {"phone": "+79990000000"},
    }

    response_first = client.post("/api/events/purchase", json=payload)
    response_second = client.post("/api/events/purchase", json=payload)

    assert response_first.status_code == 200
    assert response_first.json()["idempotent"] is False
    assert response_second.status_code == 200
    assert response_second.json()["idempotent"] is True

    count = db_session.execute(text("SELECT COUNT(*) FROM conversion_events")).scalar_one()
    assert count == 1
