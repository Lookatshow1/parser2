from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import Optional, Any, List

from pydantic import BaseModel, Field, model_validator

from app.db.models import Platform, SyncRunType, SyncRunStatus, ConnectionStatus


def validate_credentials_for_platform(platform: Platform, credentials_json: dict) -> None:
    if platform == Platform.yandex:
        if not credentials_json.get("token"):
            raise ValueError("Yandex credentials require 'token'")
    elif platform == Platform.ozon:
        if not credentials_json.get("client_id") or not credentials_json.get("client_secret"):
            raise ValueError("Ozon credentials require 'client_id' and 'client_secret'")
    elif platform == Platform.vk:
        if not credentials_json.get("access_token") or not credentials_json.get("version"):
            raise ValueError("VK credentials require 'access_token' and 'version'")
    elif platform == Platform.stub:
        return


class ConnectionTestRequest(BaseModel):
    platform: Platform
    credentials_json: dict

    @model_validator(mode="after")
    def _validate_credentials(self):
        validate_credentials_for_platform(self.platform, self.credentials_json)
        return self


class ConnectionTestResponse(BaseModel):
    ok: bool


class ConnectionCreateRequest(BaseModel):
    organization_id: int | None = None
    advertiser_id: int | None = None
    platform: Platform
    name: str | None = None
    credentials_json: dict

    @model_validator(mode="after")
    def _validate_credentials(self):
        validate_credentials_for_platform(self.platform, self.credentials_json)
        return self


class ConnectionOut(BaseModel):
    id: int
    organization_id: int
    advertiser_id: int | None = None
    platform: Platform
    name: str | None = None
    status: ConnectionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectionListResponse(BaseModel):
    items: list[ConnectionOut]


class ConnectionSyncRequest(BaseModel):
    date_from: date
    date_to: date
    force: bool = False


class HealthDb(BaseModel):
    ok: bool


class HealthMigrations(BaseModel):
    ok: bool
    current: str | None = None
    head: str | None = None


class HealthResponse(BaseModel):
    status: str
    db: HealthDb
    migrations: HealthMigrations


class HealthzResponse(BaseModel):
    status: str
    db: str


class ContactInfo(BaseModel):
    phone: str | None = None
    email: str | None = None


class EventBase(BaseModel):
    event_id: UUID
    occurred_at: datetime
    landing_url: str
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None
    contact: ContactInfo | None = None


class LeadEventRequest(EventBase):
    pass


class PurchaseEventRequest(EventBase):
    value: int = Field(..., ge=0)


class EventResponse(BaseModel):
    ok: bool
    idempotent: bool


class PlanCreateRequest(BaseModel):
    advertiser_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    platform: Platform
    budget: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="RUB", min_length=1, max_length=10)
    start_date: date | None = None
    end_date: date | None = None
    internal_code: str | None = Field(default=None, max_length=64)


class PlanResponse(BaseModel):
    id: int
    advertiser_id: int
    name: str
    platform: Platform
    budget: Decimal | None = None
    currency: str
    start_date: date | None = None
    end_date: date | None = None
    internal_code: str | None = None
    created_at: datetime
    updated_at: datetime


class PlanListResponse(BaseModel):
    items: list[PlanResponse]



class StartTestResponse(BaseModel):
    experiment_id: int
    creatives_count: int
    budgets_count: int


class StartTestRequest(BaseModel):
    budget: int = Field(..., gt=0)


class ComplianceRegisterRequest(BaseModel):
    platform: Platform
    creative_variant_id: int
    token: str


class ComplianceRegisterResponse(BaseModel):
    ok: bool


class YandexReportsSyncRequest(BaseModel):
    connection_id: int
    date_from: datetime
    date_to: datetime
    granularity: str = "daily"


class YandexReportsSyncResponse(BaseModel):
    rows: int
    saved: int


class VkStatsSyncRequest(BaseModel):
    connection_id: int
    plan_id: int
    account_id: int
    ids: list[int]
    ids_type: str
    date_from: datetime
    date_to: datetime



class VkStatsSyncResponse(BaseModel):
    rows: int
    saved: int


class YandexSyncMetricsResponse(BaseModel):
    job_id: str


class YandexSyncMetricsRequest(BaseModel):
    connection_id: int
    plan_id: int
    date_from: datetime
    date_to: datetime



class VkFetchRawRequest(BaseModel):
    connection_id: int
    method: str
    params: dict | None = None


class VkFetchRawResponse(BaseModel):
    data: dict


class ApiVersionResponse(BaseModel):
    version: str


class ApiCapabilitiesResponse(BaseModel):
    platforms: list[str]
    operations: dict[str, bool]


class DevSeedResponse(BaseModel):
    advertiser_id: int
    plan_id: int
    experiment_id: int


class DashboardTotals(BaseModel):
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int


class DashboardDailyItem(BaseModel):
    date: date
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int


class DashboardSummaryResponse(BaseModel):
    connection_id: int
    date_from: date
    date_to: date
    totals: DashboardTotals
    daily: list[DashboardDailyItem]


class ErirDevRegisterRequest(BaseModel):
    organization_id: int | None = None
    connection_id: int | None = None
    payload_json: dict


class ErirDevRegisterResponse(BaseModel):
    job_run_id: int
    erir_event_id: int
    status: str


class ExperimentCreateRequest(BaseModel):
    plan_id: int
    budget: int
    platforms: list[Platform] | None = None


class ExperimentResponse(BaseModel):
    id: int
    status: str


class ExperimentListItem(BaseModel):
    id: int
    status: str
    plan_id: int | None
    total_budget: int | None


class ExperimentListResponse(BaseModel):
    items: list[ExperimentListItem]


class ExperimentCloseResponse(BaseModel):
    job_id: str


class ExperimentReportResponse(BaseModel):
    experiment_id: int
    status: str
    rounds: list[dict]
    metrics: dict


class ExperimentDetailResponse(BaseModel):
    id: int
    status: str
    plan_id: int | None
    total_budget: int | None
    platforms: list[str] | None


class MetricsSummaryResponse(BaseModel):
    plan_id: int
    date_from: str
    date_to: str
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int
    cpc: float | None = None
    cpl: float | None = None
    cpa: float | None = None


class ExperimentCampaignItem(BaseModel):
    platform: Platform
    campaign_external_id: str


class ExperimentCampaignsRequest(BaseModel):
    items: list[ExperimentCampaignItem]


class ExperimentCampaignsResponse(BaseModel):
    items: list[ExperimentCampaignItem]
    total: int


class MetricAggregateItem(BaseModel):
    date: date | None = None
    campaign_external_id: str | None = None
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None


class MetricAggregateResponse(BaseModel):
    items: list[MetricAggregateItem]


class ExperimentSummaryResponse(BaseModel):
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None


class SyncRunCreateRequest(BaseModel):
    platform: Platform
    run_type: SyncRunType
    date_from: date | None = None
    date_to: date | None = None


class ConnectionSyncRunCreateRequest(BaseModel):
    connection_id: int
    params_json: dict | None = None


class SyncRunResponse(BaseModel):
    id: int
    organization_id: int
    experiment_id: int | None = None
    connection_id: int | None = None
    platform: Platform
    run_type: SyncRunType
    status: SyncRunStatus
    params_json: dict
    result_json: dict | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_text: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SyncRunListResponse(BaseModel):
    items: list[SyncRunResponse]
    total: int
