from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.schemas import (
    ExperimentCampaignsResponse,
    ExperimentCampaignItem,
    MetricAggregateResponse,
    ExperimentSummaryResponse,
    ExperimentCreateRequest,
    ExperimentResponse,
    ExperimentListResponse,
    ExperimentDetailResponse,
    ExperimentCloseResponse,
    ExperimentReportResponse,
    SyncRunCreateRequest,
    SyncRunResponse,
    SyncRunListResponse
)
from app.db.models import Platform, Experiment, ExperimentStatus, CampaignPlan, SyncRun, SyncRunStatus
from app.db.session import get_db
from app.services.sync_service import sync_yandex_campaigns, sync_yandex_metrics
from app.services.metrics_service import get_experiment_campaigns, get_experiment_metrics, get_experiment_summary
from app.workers.sync_tasks import execute_sync_run

router = APIRouter(prefix="/experiments", tags=["experiments"])

@router.post("/", response_model=ExperimentResponse)
def create_experiment(item: ExperimentCreateRequest, db: Session = Depends(get_db)):
    # Basic creation logic
    plan = db.query(CampaignPlan).get(item.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    exp = Experiment(
        plan_id=item.plan_id,
        total_budget=item.budget,
        platforms=item.platforms or [],
        status=ExperimentStatus.draft
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp

@router.get("/", response_model=ExperimentListResponse)
def list_experiments(db: Session = Depends(get_db)):
    items = db.query(Experiment).all()
    return {"items": items}

@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    exp = db.query(Experiment).get(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp

# --- Sync APIs ---

@router.post("/{experiment_id}/sync", response_model=SyncRunResponse)
def create_sync_run(
    experiment_id: int,
    item: SyncRunCreateRequest,
    db: Session = Depends(get_db)
):
    exp = db.query(Experiment).get(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    params = {}
    if item.date_from:
        params["date_from"] = item.date_from.isoformat()
    if item.date_to:
        params["date_to"] = item.date_to.isoformat()

    run = SyncRun(
        experiment_id=experiment_id,
        platform=item.platform,
        run_type=item.run_type,
        status=SyncRunStatus.queued,
        params_json=params
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Enqueue task
    execute_sync_run.delay(run.id)

    return run

@router.get("/{experiment_id}/sync-runs", response_model=SyncRunListResponse)
def list_sync_runs(
    experiment_id: int,
    platform: Optional[Platform] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(SyncRun).filter(SyncRun.experiment_id == experiment_id)
    if platform:
        query = query.filter(SyncRun.platform == platform)

    total = query.count()
    items = query.order_by(desc(SyncRun.created_at)).limit(limit).offset(offset).all()

    return {"items": items, "total": total}

# --- Legacy Sync APIs (Thin Wrappers) ---

@router.post("/{experiment_id}/sync/yandex/campaigns")
def api_sync_campaigns(experiment_id: int, db: Session = Depends(get_db)):
    # Thin wrapper: create sync run and execute immediately (or enqueue)
    # For backward compatibility, we can just call the service directly
    # OR create a SyncRun and wait.
    # Let's call service directly to not break existing tests that expect immediate result
    return sync_yandex_campaigns(db, experiment_id)

@router.post("/{experiment_id}/sync/yandex/metrics")
def api_sync_metrics(experiment_id: int, date_from: date, date_to: date, db: Session = Depends(get_db)):
    return sync_yandex_metrics(db, experiment_id, date_from, date_to)

# --- Read APIs ---

@router.get("/{experiment_id}/campaigns", response_model=ExperimentCampaignsResponse)
def list_experiment_campaigns(
    experiment_id: int,
    platform: Platform = Platform.yandex,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    items, total = get_experiment_campaigns(db, experiment_id, platform, limit, offset)
    return {
        "items": [
            ExperimentCampaignItem(
                platform=i.platform,
                campaign_external_id=i.campaign_external_id
            ) for i in items
        ],
        "total": total
    }

@router.get("/{experiment_id}/metrics", response_model=MetricAggregateResponse)
def get_metrics(
    experiment_id: int,
    date_from: date,
    date_to: date,
    platform: Platform = Platform.yandex,
    group_by: str = Query("day", regex="^(day|campaign|day_campaign)$"),
    campaign_external_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    items = get_experiment_metrics(
        db, experiment_id, date_from, date_to, platform, group_by, campaign_external_id
    )
    return {"items": items}

@router.get("/{experiment_id}/summary", response_model=ExperimentSummaryResponse)
def get_summary(
    experiment_id: int,
    date_from: date,
    date_to: date,
    platform: Platform = Platform.yandex,
    db: Session = Depends(get_db)
):
    return get_experiment_summary(db, experiment_id, date_from, date_to, platform)
