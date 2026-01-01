from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    VkStatsSyncRequest,
    VkStatsSyncResponse,
    YandexReportsSyncRequest,
    YandexReportsSyncResponse,
    YandexSyncMetricsRequest,
    YandexSyncMetricsResponse,
)
from app.connectors.vk_ads import VkAdsConnector
from app.connectors.vk_ads_client import VkApiError
from app.connectors.yandex_direct_reports import (
    YandexDirectReportsClient,
    YandexReportsError,
    parse_tsv_metrics,
)
from app.core.config import get_settings
from app.db.models import Connection, Platform
from app.db.session import get_db
from app.workers.yandex_tasks import sync_yandex_metrics

router = APIRouter(prefix="/integrations")


@router.post("/yandex/reports/sync", response_model=YandexReportsSyncResponse)
def sync_yandex_reports(
    payload: YandexReportsSyncRequest,
    session: Session = Depends(get_db),
):
    connection = session.scalar(
        select(Connection).where(Connection.id == payload.connection_id)
    )
    if connection is None or connection.platform != Platform.yandex:
        raise HTTPException(status_code=404, detail="Connection not found")

    token = connection.credentials_json.get("token")
    client_login = connection.credentials_json.get("client_login")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")

    settings = get_settings()
    client = YandexDirectReportsClient(
        token=token,
        client_login=client_login,
        base_url=settings.yandex_reports_url,
    )
    try:
        report_text = client.fetch_report(
            date_from=payload.date_from.date(),
            date_to=payload.date_to.date(),
            granularity=payload.granularity,
            skip_report_header=True,
            skip_column_header=False,
            skip_report_summary=True,
        )
    except YandexReportsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    metrics = parse_tsv_metrics(report_text, skip_header=False)
    session.add_all(metrics)
    session.commit()
    return YandexReportsSyncResponse(rows=len(metrics), saved=len(metrics))


@router.post("/vk/stats/sync", response_model=VkStatsSyncResponse)
def sync_vk_stats(payload: VkStatsSyncRequest, session: Session = Depends(get_db)):
    connection = session.scalar(
        select(Connection).where(Connection.id == payload.connection_id)
    )
    if connection is None or connection.platform != Platform.vk:
        raise HTTPException(status_code=404, detail="Connection not found")

    credentials = dict(connection.credentials_json)
    credentials.update(
        {
            "account_id": payload.account_id,
            "ids": payload.ids,
            "ids_type": payload.ids_type,
        }
    )
    connector = VkAdsConnector(credentials)
    try:
        metrics = connector.fetch_metrics(payload.date_from.date(), payload.date_to.date())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except VkApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    session.add_all(metrics)
    session.commit()
    return VkStatsSyncResponse(rows=len(metrics), saved=len(metrics))


@router.post("/yandex/sync-metrics", response_model=YandexSyncMetricsResponse)
def sync_yandex_metrics_job(payload: YandexSyncMetricsRequest):
    result = sync_yandex_metrics.delay(payload.date_from.date().isoformat(), payload.date_to.date().isoformat())
    return YandexSyncMetricsResponse(job_id=result.id)
