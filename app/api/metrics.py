from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas import MetricsSummaryResponse
from app.db.models import MetricSnapshot
from app.db.session import get_db

router = APIRouter(prefix="/metrics")


@router.get("/summary", response_model=MetricsSummaryResponse)
def metrics_summary(experiment_id: int = Query(...), session: Session = Depends(get_db)):
    metrics = (
        session.query(
            MetricSnapshot.date,
            MetricSnapshot.platform,
            func.sum(MetricSnapshot.impressions).label("impressions_sum"),
            func.sum(MetricSnapshot.clicks).label("clicks_sum"),
            func.sum(MetricSnapshot.spend).label("spend_sum"),
        )
        .group_by(MetricSnapshot.date, MetricSnapshot.platform)
        .all()
    )
    return MetricsSummaryResponse(
        experiment_id=experiment_id,
        metrics=[
            {
                "date": metric.date.isoformat(),
                "platform": metric.platform.value,
                "impressions": metric.impressions_sum,
                "clicks": metric.clicks_sum,
                "spend": metric.spend_sum,
            }
            for metric in metrics
        ],
    )
