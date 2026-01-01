from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models import Platform


class ConnectionTestRequest(BaseModel):
    platform: Platform
    credentials_json: dict


class ConnectionTestResponse(BaseModel):
    ok: bool


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


class StartTestResponse(BaseModel):
    experiment_id: int
    creatives_count: int
    budgets_count: int


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


class ExperimentCreateRequest(BaseModel):
    project_id: int
    total_budget: int
    platforms: list[Platform]


class ExperimentResponse(BaseModel):
    id: int
    status: str


class ExperimentCloseResponse(BaseModel):
    job_id: str


class ExperimentReportResponse(BaseModel):
    experiment_id: int
    status: str
    rounds: list[dict]
