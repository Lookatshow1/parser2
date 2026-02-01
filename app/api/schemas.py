from datetime import datetime, date as dt_date
from decimal import Decimal
from uuid import UUID
from typing import Optional, Any, List

from pydantic import BaseModel, Field, model_validator, EmailStr, ValidationError

from app.db.models import Platform, SyncRunType, SyncRunStatus, ConnectionStatus
from app.db.models import MembershipRole
from app.connectors.credentials import get_credentials_model


def validate_credentials_for_platform(platform: Platform, credentials_json: dict) -> None:
    if credentials_json and credentials_json.get("mock") is True:
        return
    if platform == Platform.yandex and not (credentials_json or {}).get("token"):
        return
    try:
        model = get_credentials_model(platform)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    try:
        model.model_validate(credentials_json or {})
    except ValidationError as exc:
        missing_fields = [err["loc"][-1] for err in exc.errors() if err.get("type") == "missing"]
        if missing_fields:
            raise ValueError(f"Missing fields: {', '.join(missing_fields)}") from exc
        raise ValueError(exc.errors()[0]["msg"]) from exc


class ConnectionTestRequest(BaseModel):
    platform: Platform
    credentials_json: dict

    @model_validator(mode="after")
    def _validate_credentials(self):
        validate_credentials_for_platform(self.platform, self.credentials_json)
        return self


class ConnectionTestResponse(BaseModel):
    ok: bool
    message: str | None = None
    error_code: str | None = None


class ConnectionCreateRequest(BaseModel):
    organization_id: int | None = None
    advertiser_id: int | None = None
    platform: Platform
    name: str | None = None
    credentials_json: dict
    credentials_mode: str | None = None
    auto_sync_enabled: bool = True
    auto_sync_every_minutes: int = Field(default=1440, ge=1)
    auto_sync_window_days: int = Field(default=3, ge=1)

    @model_validator(mode="after")
    def _validate_credentials(self):
        if self.credentials_mode != "dev":
            validate_credentials_for_platform(self.platform, self.credentials_json)
        return self


class ConnectionOut(BaseModel):
    id: int
    organization_id: int
    advertiser_id: int | None = None
    platform: Platform
    name: str | None = None
    status: ConnectionStatus
    credentials_present: bool
    last_sync_status: SyncRunStatus | None = None
    last_sync_finished_at: datetime | None = None
    auto_sync_enabled: bool
    auto_sync_every_minutes: int
    auto_sync_window_days: int
    last_auto_sync_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectionListResponse(BaseModel):
    items: list[ConnectionOut]


class ConnectionUpdateRequest(BaseModel):
    name: str | None = None
    auto_sync_enabled: bool | None = None
    auto_sync_every_minutes: int | None = Field(default=None, ge=1)
    auto_sync_window_days: int | None = Field(default=None, ge=1)


class ConnectionSyncRequest(BaseModel):
    date_from: dt_date | None = None
    date_to: dt_date | None = None
    force: bool = False


class MetricSnapshotOut(BaseModel):
    date: dt_date
    level: str
    campaign_external_id: str
    ad_group_external_id: str | None = None
    ad_external_id: str | None = None
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int

    class Config:
        from_attributes = True


class MetricSnapshotListResponse(BaseModel):
    items: list[MetricSnapshotOut]


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    invite_token: str | None = None


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int


class AuthRefreshRequest(BaseModel):
    refresh_token: str


class AuthRefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class AuthMeResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    active_organization_id: int | None = None

    class Config:
        from_attributes = True


class OrganizationCreateRequest(BaseModel):
    name: str


class OrganizationSwitchRequest(BaseModel):
    organization_id: int


class OrganizationOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MembershipOut(BaseModel):
    organization_id: int
    role: MembershipRole

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    items: list[OrganizationOut]


class OrgInviteCreateRequest(BaseModel):
    email: EmailStr
    role: MembershipRole
    expires_in_days: int | None = 7


class OrgInviteAcceptRequest(BaseModel):
    token: str


class OrgInviteOut(BaseModel):
    id: int
    organization_id: int
    invited_email: EmailStr
    role: MembershipRole
    status: str
    expires_at: datetime
    accepted_at: datetime | None = None
    accepted_by_user_id: int | None = None
    revoked_at: datetime | None = None
    revoked_by_user_id: int | None = None
    created_by_user_id: int
    created_at: datetime
    sent_at: datetime | None = None
    send_count: int = 0
    last_error: str | None = None

    class Config:
        from_attributes = True


class OrgInviteCreateResponse(OrgInviteOut):
    invite_token: str
    join_url: str | None = None


class OrgInviteAcceptResponse(BaseModel):
    organization_id: int
    organization_name: str
    role: MembershipRole
    active_organization_id: int | None = None


class OrgInviteListResponse(BaseModel):
    items: list[OrgInviteOut]


class OrgInviteResendRequest(BaseModel):
    expires_in_days: int | None = None


class OrgInviteResendResponse(BaseModel):
    id: int
    sent_at: datetime | None = None
    send_count: int
    last_error: str | None = None


class OrgMemberOut(BaseModel):
    user_id: int
    email: EmailStr
    role: MembershipRole
    joined_at: datetime
    is_you: bool = False


class OrgAuditEventOut(BaseModel):
    id: int
    organization_id: int
    actor_user_id: int | None = None
    action: str
    subject_type: str | None = None
    subject_id: int | None = None
    meta: dict
    ip: str | None = None
    user_agent: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrgAuditListResponse(BaseModel):
    items: list[OrgAuditEventOut]
    total: int


class InvitePreviewResponse(BaseModel):
    organization_id: int | None = None
    organization_name: str | None = None
    invited_email: EmailStr | None = None
    role: MembershipRole | None = None
    expires_at: datetime | None = None
    status: str


class OrgMemberRoleUpdateRequest(BaseModel):
    role: MembershipRole


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
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    internal_code: str | None = Field(default=None, max_length=64)


class PlanResponse(BaseModel):
    id: int
    advertiser_id: int
    organization_id: int
    connection_id: int | None = None
    name: str
    platform: Platform
    budget: Decimal | None = None
    currency: str
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    internal_code: str | None = None
    status: str = "draft"
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


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
    user_id: int | None = None
    org_a_id: int | None = None
    org_b_id: int | None = None
    advertiser_id: int
    plan_id: int
    experiment_id: int


class DemoSeedResponse(BaseModel):
    demo_user_email: str
    demo_password: str | None = None
    org_id: int
    connection_ids: list[int]
    period_from: dt_date
    period_to: dt_date


class DashboardTotals(BaseModel):
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None
    cpa: float | None = None
    roas: float | None = None


class DashboardDailyItem(BaseModel):
    date: dt_date
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None
    cpa: float | None = None
    roas: float | None = None


class DashboardConnectionTotals(BaseModel):
    connection_id: int
    totals: DashboardTotals


class DashboardSummaryResponse(BaseModel):
    connection_id: int | None = None
    date_from: dt_date
    date_to: dt_date
    totals: DashboardTotals
    daily: list[DashboardDailyItem]
    connections: list[DashboardConnectionTotals] | None = None


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
    date: dt_date | None = None
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


class MetricPoint(BaseModel):
    date: dt_date
    value: int


class MetricTimeseriesItem(BaseModel):
    date: dt_date
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None
    cpa: float | None = None
    roas: float | None = None


class MetricTimeseriesTotals(BaseModel):
    impressions: int
    clicks: int
    spend: int
    leads: int
    purchases: int
    revenue: int
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None
    cpa: float | None = None
    roas: float | None = None


class MetricTimeseriesResponse(BaseModel):
    date_from: dt_date
    date_to: dt_date
    items: list[MetricTimeseriesItem]
    totals: MetricTimeseriesTotals


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
    date_from: dt_date | None = None
    date_to: dt_date | None = None


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


# --- Builder Schemas ---

class BuilderCampaignCreateRequest(BaseModel):
    platform: Platform
    name: str = Field(..., min_length=1, max_length=255)
    status: str = "draft"


class BuilderCampaignUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    status: str | None = None


class BuilderCampaignOut(BaseModel):
    id: int
    experiment_id: int
    platform: Platform
    name: str
    status: str
    external_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BuilderAdGroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    status: str = "draft"


class BuilderAdGroupUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    status: str | None = None


class BuilderAdGroupOut(BaseModel):
    id: int
    campaign_id: int
    name: str
    status: str
    external_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BuilderAdCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    title: str | None = None
    text: str | None = None
    base_url: str | None = None
    utm_json: dict = Field(default_factory=dict)
    status: str = "draft"


class BuilderAdUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    title: str | None = None
    text: str | None = None
    base_url: str | None = None
    utm_json: dict | None = None
    status: str | None = None


class BuilderAdOut(BaseModel):
    id: int
    ad_group_id: int
    name: str
    title: str | None = None
    text: str | None = None
    base_url: str | None = None
    utm_json: dict
    final_url: str | None = None
    status: str
    external_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BuilderTreeAd(BuilderAdOut):
    pass


class BuilderTreeAdGroup(BuilderAdGroupOut):
    ads: list[BuilderTreeAd] = []


# --- Wizard Schemas ---

class WizardAdCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    title: str | None = Field(None, max_length=255)
    text: str | None = None
    landing_url: str | None = None
    creative_json: dict | None = None  # For image_url etc.

class WizardAdGroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    budget_daily: Decimal | None = Field(None, ge=0)
    bid_strategy: str | None = None
    targeting_json: dict = Field(default_factory=dict)
    ads: list[WizardAdCreateRequest] = []

class WizardCampaignCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    platform: Platform
    objective: str | None = None
    budget_total: Decimal | None = Field(None, ge=0)
    budget_daily: Decimal | None = Field(None, ge=0)
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    ad_groups: list[WizardAdGroupCreateRequest] = []



class BuilderTreeCampaign(BuilderCampaignOut):
    ad_groups: list[BuilderTreeAdGroup] = []


class BuilderTreeResponse(BaseModel):
    campaigns: list[BuilderTreeCampaign]

# --- Campaigns Schemas ---

class CampaignCreateRequest(BaseModel):
    platform: Platform
    name: str = Field(..., min_length=1, max_length=255)
    objective: str | None = None
    status: str = "draft"
    budget_total: Decimal | None = None
    budget_daily: Decimal | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None


class CampaignUpdateRequest(BaseModel):
    platform: Platform | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    objective: str | None = None
    status: str | None = None
    budget_total: Decimal | None = None
    budget_daily: Decimal | None = None
    start_date: dt_date | None = None
    end_date: dt_date | None = None


class CampaignOut(BaseModel):
    id: int
    organization_id: int
    connection_id: int
    platform: Platform
    name: str
    objective: str | None
    status: str
    budget_total: Decimal | None
    budget_daily: Decimal | None
    start_date: dt_date | None
    end_date: dt_date | None
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    items: list[CampaignOut]
    total: int


class CampaignSummaryResponse(CampaignOut):
    ad_groups_count: int
    ads_count: int


class CampaignAdGroupCreateRequest(BaseModel):
    campaign_id: int
    name: str = Field(..., min_length=1, max_length=255)
    status: str = "draft"
    bid_strategy: str | None = None
    budget_daily: Decimal | None = None
    targeting_json: dict = Field(default_factory=dict)


class CampaignAdGroupUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    status: str | None = None
    bid_strategy: str | None = None
    budget_daily: Decimal | None = None
    targeting_json: dict | None = None


class CampaignAdGroupOut(BaseModel):
    id: int
    campaign_id: int
    name: str
    status: str
    bid_strategy: str | None
    budget_daily: Decimal | None
    targeting_json: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignAdGroupListResponse(BaseModel):
    items: list[CampaignAdGroupOut]
    total: int


class CampaignAdCreateRequest(BaseModel):
    ad_group_id: int
    name: str = Field(..., min_length=1, max_length=255)
    status: str = "draft"
    creative_json: dict = Field(default_factory=dict)
    landing_url: str | None = None


class CampaignAdUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    status: str | None = None
    creative_json: dict | None = None
    landing_url: str | None = None


class CampaignAdOut(BaseModel):
    id: int
    ad_group_id: int
    connection_id: int
    name: str
    status: str
    creative_json: dict
    landing_url: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignAdListResponse(BaseModel):
    items: list[CampaignAdOut]
    total: int


class CampaignTreeAd(CampaignAdOut):
    pass


class CampaignTreeAdGroup(CampaignAdGroupOut):
    ads: list[CampaignTreeAd] = []


class CampaignTree(CampaignOut):
    ad_groups: list[CampaignTreeAdGroup] = []


class CampaignTreeResponse(BaseModel):
    campaign: CampaignTree

class CampaignEventOut(BaseModel):
    id: int
    organization_id: int
    entity_type: str
    entity_id: int
    action: str
    payload_json: dict
    created_by_user_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Catalog Schemas ---

class AdCampaignOut(BaseModel):
    id: int
    connection_id: int
    platform: Platform
    external_id: str
    name: str
    updated_at: datetime

    class Config:
        from_attributes = True

class AdAdGroupOut(BaseModel):
    id: int
    connection_id: int
    platform: Platform
    external_id: str
    campaign_external_id: str
    name: str
    updated_at: datetime

    class Config:
        from_attributes = True

class AdAdOut(BaseModel):
    id: int
    connection_id: int
    platform: Platform
    external_id: str
    ad_group_external_id: str
    campaign_external_id: str
    name: str
    target_url: str | None = None
    final_url: str | None = None
    url_status: str | None = None
    utm_applied_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True

class UtmSettingsOut(BaseModel):
    organization_id: int
    utm_source: str
    utm_medium: str
    utm_campaign_tpl: str
    utm_content_tpl: str
    utm_term_tpl: str | None = None
    auto_update_ads: bool = False

    class Config:
        from_attributes = True

class OrgProfileOut(BaseModel):
    organization_id: int
    legal_type: str | None = None
    legal_name: str | None = None
    inn: str | None = None
    kpp: str | None = None
    ogrn: str | None = None
    ogrnip: str | None = None
    legal_address: str | None = None
    email_for_docs: str | None = None
    phone: str | None = None
    timezone: str
    currency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrgProfileUpdate(BaseModel):
    legal_type: str | None = None
    legal_name: str | None = None
    inn: str | None = None
    kpp: str | None = None
    ogrn: str | None = None
    ogrnip: str | None = None
    legal_address: str | None = None
    email_for_docs: str | None = None
    phone: str | None = None
    timezone: str | None = None
    currency: str | None = None

class UtmSettingsUpdate(BaseModel):
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign_tpl: str | None = None
    utm_content_tpl: str | None = None
    utm_term_tpl: str | None = None
    auto_update_ads: bool | None = None

class UtmBuildRequest(BaseModel):
    url: str
    platform: Platform | None = None
    campaign_external_id: str | None = None
    ad_group_external_id: str | None = None
    ad_external_id: str | None = None

class UtmBuildResponse(BaseModel):
    final_url: str


class UtmRuleOut(BaseModel):
    id: int
    organization_id: int
    is_enabled: bool
    match_platform: Platform | None = None
    match_connection_id: int | None = None
    match_campaign_contains: str | None = None
    match_ad_group_contains: str | None = None
    match_ad_contains: str | None = None
    template_json: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UtmRuleCreate(BaseModel):
    is_enabled: bool | None = True
    match_platform: Platform | None = None
    match_connection_id: int | None = None
    match_campaign_contains: str | None = None
    match_ad_group_contains: str | None = None
    match_ad_contains: str | None = None
    template_json: dict = Field(default_factory=dict)


class UtmRuleUpdate(BaseModel):
    is_enabled: bool | None = None
    match_platform: Platform | None = None
    match_connection_id: int | None = None
    match_campaign_contains: str | None = None
    match_ad_group_contains: str | None = None
    match_ad_contains: str | None = None
    template_json: dict | None = None


class UtmStatusOut(BaseModel):
    ok: int = 0
    invalid_url: int = 0
    blocked_scheme: int = 0
    missing_url: int = 0
    unknown: int = 0


class AutomationSettingsOut(BaseModel):
    organization_id: int
    is_enabled: bool
    run_interval_minutes: int
    last_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AutomationSettingsUpdate(BaseModel):
    is_enabled: bool | None = None
    run_interval_minutes: int | None = None


class AutomationRunOut(BaseModel):
    id: int
    organization_id: int
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result_json: dict
    error_text: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AutomationActionOut(BaseModel):
    id: int
    organization_id: int
    run_id: int | None = None
    recommendation_id: int | None = None
    action_type: str
    status: str
    title: str
    description: str
    payload_json: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Metrics Breakdown ---

class MetricsBreakdownItem(BaseModel):
    dimension: str
    id: int | None = None
    external_id: str
    name: str | None = None
    platform: Platform
    spend: int
    impressions: int
    clicks: int
    leads: int
    purchases: int
    revenue: int
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None
    cpa: float | None = None
    roas: float | None = None

class MetricsBreakdownResponse(BaseModel):
    items: list[MetricsBreakdownItem]
    total: int

# --- Recommendations ---

class RecommendationOut(BaseModel):
    id: int
    organization_id: int
    connection_id: int | None = None
    subject_type: str
    subject_id: int | None = None
    subject_name: str | None = None
    code: str
    severity: str
    title: str
    description: str
    action: str
    meta_json: dict
    valid_from: dt_date
    valid_to: dt_date
    created_at: str
    resolved_at: str | None = None

    class Config:
        from_attributes = True

class RecommendationListResponse(BaseModel):
    items: list[RecommendationOut]
    total: int

class RecomputeRequest(BaseModel):
    date_from: dt_date
    date_to: dt_date
    connection_ids: list[int] | None = None

# --- Change Plans ---

class ChangePlanItemOut(BaseModel):
    id: int
    subject_type: str
    subject_id: int
    action_type: str
    params_json: dict
    status: str
    error: str | None = None

    class Config:
        from_attributes = True

class ChangePlanOut(BaseModel):
    id: int
    organization_id: int
    connection_id: int
    title: str
    status: str
    date_from: dt_date | None = None
    date_to: dt_date | None = None
    created_at: datetime
    applied_at: datetime | None = None
    items: list[ChangePlanItemOut] = []

    class Config:
        from_attributes = True

class CreatePlanRequest(BaseModel):
    connection_id: int
    title: str
    date_from: dt_date | None = None
    date_to: dt_date | None = None

class AddItemRequest(BaseModel):
    subject_type: str
    subject_id: int
    action_type: str
    params: dict = {}

# --- Unified Dashboard ---

class UnifiedSeriesPoint(BaseModel):
    date: dt_date
    raw: dict[str, float]
    norm: dict[str, float]
    index: float

class UnifiedDashboardResponse(BaseModel):
    date_from: dt_date
    date_to: dt_date
    channel: str
    available_channels: list[dict]
    series: list[UnifiedSeriesPoint]
    totals: dict[str, float]
    kpi: dict[str, float | None]

class DashboardChannel(BaseModel):
    key: str
    title: str

# --- KPI Dashboard ---

class KpiTimeseriesItem(BaseModel):
    date: str
    impressions: int
    clicks: int
    conversions: int
    spend: int
    impressions_index: float | None = None
    clicks_index: float | None = None
    conversions_index: float | None = None
    spend_index: float | None = None

class KpiTimeseriesMeta(BaseModel):
    date_from: str
    date_to: str
    mode: str
    platform: str | None = None
    connection_ids: list[int] = []

class KpiTimeseriesResponse(BaseModel):
    items: list[KpiTimeseriesItem]
    meta: KpiTimeseriesMeta

class KpiSummaryResponse(BaseModel):
    impressions: int
    clicks: int
    conversions: int
    spend: int
    ctr: float | None = None
    cpc: float | None = None
    cpa: float | None = None
    currency: str = "RUB"
