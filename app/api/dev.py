from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import DevSeedResponse
from app.core.config import get_settings
from app.db.models import Advertiser, CampaignPlan, Experiment
from app.db.session import get_db

router = APIRouter(prefix="/dev")


@router.post("/seed", response_model=DevSeedResponse)
def seed_dev(session: Session = Depends(get_db)):
    settings = get_settings()
    if settings.env != "dev":
        raise HTTPException(status_code=404, detail="Not found")

    advertiser = Advertiser(name="Dev Advertiser")
    session.add(advertiser)
    session.flush()
    plan = CampaignPlan(advertiser_id=advertiser.id, name="Dev Plan", platform="yandex")
    session.add(plan)
    session.flush()
    experiment = Experiment(plan_id=plan.id, total_budget=10000, platforms=["yandex", "ozon", "vk"])
    session.add(experiment)
    session.commit()

    return DevSeedResponse(
        advertiser_id=advertiser.id,
        plan_id=plan.id,
        experiment_id=experiment.id,
    )
