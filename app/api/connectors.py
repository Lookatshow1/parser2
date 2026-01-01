from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.vk_ads import VkAdsConnector
from app.core.config import get_settings
from app.db.models import Connection, Platform
from app.db.session import get_db
from app.api.schemas import (
    VkFetchRawRequest,
    VkFetchRawResponse,
    YandexSyncMetricsRequest,
    YandexSyncMetricsResponse,
)
from app.workers.yandex_tasks import sync_yandex_metrics

router = APIRouter(prefix="/connectors")


@router.post("/yandex/sync_metrics", response_model=YandexSyncMetricsResponse)
def sync_yandex(payload: YandexSyncMetricsRequest):
    result = sync_yandex_metrics.delay(payload.date_from.date().isoformat(), payload.date_to.date().isoformat())
    return YandexSyncMetricsResponse(job_id=result.id)


@router.post("/vk/fetch_raw", response_model=VkFetchRawResponse)
def fetch_vk_raw(payload: VkFetchRawRequest, session: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.dev_mode:
        raise HTTPException(status_code=404, detail="Not found")

    connection = session.scalar(select(Connection).where(Connection.id == payload.connection_id))
    if connection is None or connection.platform != Platform.vk:
        raise HTTPException(status_code=404, detail="Connection not found")

    connector = VkAdsConnector(connection.credentials_json)
    try:
        data = connector.fetch_raw(payload.method, connection.credentials_json, payload.params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return VkFetchRawResponse(data=data)
