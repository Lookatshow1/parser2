from sqlalchemy import text

from app.db.models import CampaignPlan, CreativeVariant, Experiment, Platform


def seed_creative(session):
    plan = CampaignPlan(url="https://example.com", advertiser_id=1)
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
        meta_json={},
    )
    session.add(creative)
    session.commit()
    session.refresh(creative)
    return creative


def test_register_compliance_token(client, db_session):
    creative = seed_creative(db_session)

    payload = {
        "platform": "ozon",
        "creative_variant_id": creative.id,
        "token": "compliance-token-123",
    }

    response = client.post("/api/compliance/register", json=payload)

    assert response.status_code == 200
    assert response.json() == {"ok": True}

    token = db_session.execute(
        text("SELECT compliance_token FROM creative_variants WHERE id = :id"),
        {"id": creative.id},
    ).scalar_one()
    assert token == "compliance-token-123"
