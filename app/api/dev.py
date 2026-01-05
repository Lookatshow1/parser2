from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import DevSeedResponse
from app.core.config import get_settings
from app.db.models import Advertiser, CampaignPlan, Experiment, Connection, Platform
from app.db.session import get_db

router = APIRouter(prefix="/dev")


@router.post("/seed", response_model=DevSeedResponse)
def seed_dev(session: Session = Depends(get_db)):
    settings = get_settings()
    if settings.env != "dev":
        raise HTTPException(status_code=404, detail="Not found")
    organization_id = settings.default_organization_id

    advertiser = Advertiser(name="Dev Advertiser")
    session.add(advertiser)
    session.flush()

    # Create connection
    connection = Connection(
        organization_id=organization_id,
        advertiser_id=advertiser.id,
        platform=Platform.yandex,
        name="Dev Connection",
        credentials_json={"token": "dev_token"}
    )
    session.add(connection)
    session.flush()

    plan = CampaignPlan(
        organization_id=organization_id,
        advertiser_id=advertiser.id,
        name="Dev Plan",
        platform=Platform.yandex,
        connection_id=connection.id
    )
    session.add(plan)
    session.flush()

    experiment = Experiment(
        plan_id=plan.id,
        total_budget=10000,
        platforms=["yandex", "ozon", "vk"],
        organization_id=organization_id,
    )
    session.add(experiment)
    session.commit()

    return DevSeedResponse(
        advertiser_id=advertiser.id,
        plan_id=plan.id,
        experiment_id=experiment.id,
    )
