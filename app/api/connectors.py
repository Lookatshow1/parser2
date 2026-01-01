from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.vk_ads import VkAdsConnector
from app.core.config import get_settings
from app.db.models import Connection, Platform
from app.db.session import get_db
from app.workers.yandex_tasks import sync_yandex_metrics

router = APIRouter(prefix="/connectors")


@router.post("/yandex/sync_metrics")
def sync_yandex(date_from: date = Query(...), date_to: date = Query(...)):
    result = sync_yandex_metrics.delay(date_from.isoformat(), date_to.isoformat())
    return {"job_id": result.id}


@router.post("/vk/fetch_raw")
def fetch_vk_raw(
    method: str = Query(...),
    connection_id: int = Query(..., gt=0),
    session: Session = Depends(get_db),
):
    settings = get_settings()
    if not settings.dev_mode:
        raise HTTPException(status_code=404, detail="Not found")

    connection = session.scalar(select(Connection).where(Connection.id == connection_id))
    if connection is None or connection.platform != Platform.vk:
        raise HTTPException(status_code=404, detail="Connection not found")

    connector = VkAdsConnector(connection.credentials_json)
    try:
        data = connector.fetch_raw(method, connection.credentials_json)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return data
