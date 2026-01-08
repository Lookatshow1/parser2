from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.vk_ads import VkAdsConnector
from app.connectors.stub import StubConnector
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
from app.security.credentials_crypto import maybe_decrypt

router = APIRouter(prefix="/connectors")


@router.post("/yandex/sync_metrics", response_model=YandexSyncMetricsResponse, deprecated=True)
def sync_yandex(payload: YandexSyncMetricsRequest):
    result = sync_yandex_metrics.delay(
        payload.connection_id,
        payload.plan_id,
        payload.date_from.date().isoformat(),
        payload.date_to.date().isoformat(),
    )
    return YandexSyncMetricsResponse(job_id=result.id)


@router.post("/vk/fetch_raw", response_model=VkFetchRawResponse)
def fetch_vk_raw(payload: VkFetchRawRequest, session: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.dev_mode:
        raise HTTPException(status_code=404, detail="Not found")

    connection = session.scalar(select(Connection).where(Connection.id == payload.connection_id))
    if connection is None or connection.platform != Platform.vk:
        raise HTTPException(status_code=404, detail="Connection not found")

    decrypted = maybe_decrypt(connection.credentials_json)
    connector = VkAdsConnector(decrypted)
    try:
        data = connector.fetch_raw(payload.method, decrypted, payload.params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return VkFetchRawResponse(data=data)


@router.post("/stub/fetch_raw", response_model=VkFetchRawResponse)
def fetch_stub_raw(payload: VkFetchRawRequest):
    connector = StubConnector()
    return VkFetchRawResponse(data=connector.fetch_raw(payload.method, payload.params))
