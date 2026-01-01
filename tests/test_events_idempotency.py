from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import CampaignPlan, Experiment
from app.db.session import get_db
from app.main import create_app


def build_client():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), TestingSessionLocal


def seed_plan(session):
    plan = CampaignPlan(internal_code="campaign-123", url="https://example.com")
    session.add(plan)
    session.commit()
    session.refresh(plan)
    experiment = Experiment(plan_id=plan.id)
    session.add(experiment)
    session.commit()
    return plan


def test_lead_event_idempotent():
    client, session_factory = build_client()
    with session_factory() as session:
        seed_plan(session)

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

    with session_factory() as session:
        count = session.execute(text("SELECT COUNT(*) FROM conversion_events")).scalar_one()
    assert count == 1


def test_purchase_event_idempotent():
    client, session_factory = build_client()
    with session_factory() as session:
        seed_plan(session)

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

    with session_factory() as session:
        count = session.execute(text("SELECT COUNT(*) FROM conversion_events")).scalar_one()
    assert count == 1
