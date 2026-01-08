from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import DevSeedResponse
from app.core.config import get_settings
from app.db.models import Advertiser, CampaignPlan, Experiment, Connection, Platform, User, Organization, Membership, MembershipRole
from app.db.session import get_db
from app.services.auth_service import get_password_hash
from app.security.credentials_crypto import maybe_encrypt

router = APIRouter(prefix="/dev")


@router.post("/seed", response_model=DevSeedResponse)
def seed_dev(session: Session = Depends(get_db)):
    settings = get_settings()
    if settings.env != "dev":
        raise HTTPException(status_code=404, detail="Not found")

    user = session.query(User).filter(User.email == "dev@example.com").first()
    if user is None:
        user = User(
            email="dev@example.com",
            password_hash=get_password_hash("secret123"),
            is_active=True,
        )
        session.add(user)
        session.flush()

    org_a = session.query(Organization).filter(Organization.name == "Dev Org A").first()
    if org_a is None:
        org_a = Organization(name="Dev Org A")
        session.add(org_a)
        session.flush()

    org_b = session.query(Organization).filter(Organization.name == "Dev Org B").first()
    if org_b is None:
        org_b = Organization(name="Dev Org B")
        session.add(org_b)
        session.flush()

    if not session.query(Membership).filter(Membership.user_id == user.id, Membership.organization_id == org_a.id).first():
        session.add(
            Membership(user_id=user.id, organization_id=org_a.id, role=MembershipRole.owner.value)
        )
    if not session.query(Membership).filter(Membership.user_id == user.id, Membership.organization_id == org_b.id).first():
        session.add(
            Membership(user_id=user.id, organization_id=org_b.id, role=MembershipRole.owner.value)
        )
    user.active_organization_id = org_a.id

    advertiser = session.query(Advertiser).filter(Advertiser.name == "Dev Advertiser").first()
    if advertiser is None:
        advertiser = Advertiser(name="Dev Advertiser")
        session.add(advertiser)
        session.flush()

    # Create connections in different orgs
    connection_a = session.query(Connection).filter(
        Connection.organization_id == org_a.id,
        Connection.platform == Platform.yandex,
        Connection.name == "Dev Connection A",
    ).first()
    if connection_a is None:
        connection_a = Connection(
            organization_id=org_a.id,
            advertiser_id=advertiser.id,
            platform=Platform.yandex,
            name="Dev Connection A",
            credentials_json=maybe_encrypt({"token": "dev_token"}),
        )
        session.add(connection_a)
        session.flush()

    connection_b = session.query(Connection).filter(
        Connection.organization_id == org_b.id,
        Connection.platform == Platform.stub,
        Connection.name == "Dev Connection B",
    ).first()
    if connection_b is None:
        connection_b = Connection(
            organization_id=org_b.id,
            advertiser_id=advertiser.id,
            platform=Platform.stub,
            name="Dev Connection B",
            credentials_json=maybe_encrypt({}),
        )
        session.add(connection_b)
        session.flush()

    plan = session.query(CampaignPlan).filter(
        CampaignPlan.organization_id == org_a.id,
        CampaignPlan.name == "Dev Plan",
    ).first()
    if plan is None:
        plan = CampaignPlan(
            organization_id=org_a.id,
            advertiser_id=advertiser.id,
            name="Dev Plan",
            platform=Platform.yandex,
            connection_id=connection_a.id,
        )
        session.add(plan)
        session.flush()

    experiment = session.query(Experiment).filter(
        Experiment.plan_id == plan.id,
        Experiment.organization_id == org_a.id,
    ).first()
    if experiment is None:
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
