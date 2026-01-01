from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models import Platform


class ConnectionTestRequest(BaseModel):
    platform: Platform
    credentials_json: dict


class ConnectionTestResponse(BaseModel):
    ok: bool


class ConnectionCreateRequest(BaseModel):
    advertiser_id: int | None = None
    platform: Platform
    credentials_json: dict


class ConnectionResponse(BaseModel):
    id: int
    advertiser_id: int | None = None
    platform: Platform
    status: str


class ConnectionListResponse(BaseModel):
    items: list[ConnectionResponse]


class HealthResponse(BaseModel):
    status: str


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
    url: str
    business_description: str | None = None
    kpi: str | None = None
    internal_code: str | None = None


class PlanResponse(BaseModel):
    id: int
    url: str
    internal_code: str | None = None


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
    metrics: list[dict]


class ExperimentDetailResponse(BaseModel):
    id: int
    status: str
    plan_id: int | None
    total_budget: int | None
    platforms: list[str] | None


class MetricsSummaryResponse(BaseModel):
    experiment_id: int
    metrics: list[dict]
