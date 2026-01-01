from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import CampaignPlan, CreativeVariant, Experiment, Platform
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


def seed_creative(session):
    plan = CampaignPlan(url="https://example.com")
    session.add(plan)
    session.commit()
    session.refresh(plan)
    experiment = Experiment(plan_id=plan.id)
    session.add(experiment)
    session.commit()
    session.refresh(experiment)
    creative = CreativeVariant(
        experiment_id=experiment.id,
        platform=Platform.ozon,
        text="Test creative",
        image_url=None,
        meta_json=None,
    )
    session.add(creative)
    session.commit()
    session.refresh(creative)
    return creative


def test_register_compliance_token():
    client, session_factory = build_client()
    with session_factory() as session:
        creative = seed_creative(session)

    payload = {
        "platform": "ozon",
        "creative_variant_id": creative.id,
        "token": "compliance-token-123",
    }

    response = client.post("/api/compliance/register", json=payload)

    assert response.status_code == 200
    assert response.json() == {"ok": True}

    with session_factory() as session:
        token = session.execute(
            text("SELECT compliance_token FROM creative_variants WHERE id = :id"),
            {"id": creative.id},
        ).scalar_one()
    assert token == "compliance-token-123"
