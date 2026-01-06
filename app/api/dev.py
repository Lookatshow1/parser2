from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import DevSeedResponse
from app.core.config import get_settings
from app.db.models import Advertiser, CampaignPlan, Experiment, Connection, Platform, User, Organization, Membership, MembershipRole
from app.db.session import get_db
from app.services.auth_service import get_password_hash

router = APIRouter(prefix="/dev")


@router.post("/seed", response_model=DevSeedResponse)
def seed_dev(session: Session = Depends(get_db)):
    settings = get_settings()
    if settings.env != "dev":
        raise HTTPException(status_code=404, detail="Not found")

    user = User(
        email="dev@example.com",
        password_hash=get_password_hash("secret123"),
        is_active=True,
    )
    session.add(user)
    session.flush()

    org_a = Organization(name="Dev Org A")
    org_b = Organization(name="Dev Org B")
    session.add_all([org_a, org_b])
    session.flush()

    session.add(
        Membership(user_id=user.id, organization_id=org_a.id, role=MembershipRole.owner.value)
    )
    session.add(
        Membership(user_id=user.id, organization_id=org_b.id, role=MembershipRole.owner.value)
    )
    user.active_organization_id = org_a.id

    advertiser = Advertiser(name="Dev Advertiser")
    session.add(advertiser)
    session.flush()

    # Create connections in different orgs
    connection_a = Connection(
        organization_id=org_a.id,
        advertiser_id=advertiser.id,
        platform=Platform.yandex,
        name="Dev Connection A",
        credentials_json={"token": "dev_token"},
    )
    session.add(connection_a)
    session.flush()

    connection_b = Connection(
        organization_id=org_b.id,
        advertiser_id=advertiser.id,
        platform=Platform.stub,
        name="Dev Connection B",
        credentials_json={},
    )
    session.add(connection_b)
    session.flush()

    plan = CampaignPlan(
        organization_id=org_a.id,
        advertiser_id=advertiser.id,
        name="Dev Plan",
        platform=Platform.yandex,
        connection_id=connection_a.id,
    )
    session.add(plan)
    session.flush()

    experiment = Experiment(
        plan_id=plan.id,
        total_budget=10000,
        platforms=["yandex", "ozon", "vk"],
        organization_id=org_a.id,
    )
    session.add(experiment)
    session.commit()

    return DevSeedResponse(
        user_id=user.id,
        org_a_id=org_a.id,
        org_b_id=org_b.id,
        advertiser_id=advertiser.id,
        plan_id=plan.id,
        experiment_id=experiment.id,
    )
