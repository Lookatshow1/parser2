import enum
from decimal import Decimal
from datetime import datetime, date

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, LargeBinary, Numeric, String, Text, UniqueConstraint, func, Index, text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Platform-adaptive JSON type
JSONType = JSON().with_variant(PGJSONB(astext_type=Text()), "postgresql")

class Platform(str, enum.Enum):
    yandex = "yandex"
    ozon = "ozon"
    vk = "vk"
    stub = "stub"


class ConnectionStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    error = "error"


class ExperimentStatus(str, enum.Enum):
    draft = "draft"
    running = "running"
    stopped = "stopped"
    completed = "completed"


class MembershipRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active_organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Membership(Base):
    __tablename__ = "organization_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[MembershipRole] = mapped_column(String(50), nullable=False, default=MembershipRole.member.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
        Index("idx_org_members_user_id", "user_id"),
        Index("idx_org_members_org_id", "organization_id"),
    )


class OrgInvite(Base):
    __tablename__ = "org_invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    invited_email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[MembershipRole] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    send_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class OrgAuditEvent(Base):
    __tablename__ = "org_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict] = mapped_column(JSONType, nullable=False, server_default='{}')
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_org_audit_org_created_at", "organization_id", text("created_at DESC")),
        Index("idx_org_audit_org_action", "organization_id", "action"),
        Index("idx_org_audit_subject", "subject_type", "subject_id"),
    )


class Advertiser(Base):
    __tablename__ = "advertisers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    connections: Mapped[list["Connection"]] = relationship(back_populates="advertiser")
    plans: Mapped[list["CampaignPlan"]] = relationship(back_populates="advertiser")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    advertiser_id: Mapped[int | None] = mapped_column(ForeignKey("advertisers.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    advertiser: Mapped[Advertiser | None] = relationship()


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    advertiser_id: Mapped[int | None] = mapped_column(ForeignKey("advertisers.id"), nullable=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    credentials_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    credentials_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    credentials_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    auto_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    auto_sync_every_minutes: Mapped[int] = mapped_column(Integer, default=1440, server_default="1440", nullable=False)
    auto_sync_window_days: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    last_auto_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus, name="connection_status_enum", native_enum=False),
        default=ConnectionStatus.active,
        server_default=ConnectionStatus.active.value,
        nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    advertiser: Mapped[Advertiser | None] = relationship(back_populates="connections")
    plans: Mapped[list["CampaignPlan"]] = relationship(back_populates="connection")

    @property
    def credentials_present(self) -> bool:
        return bool(self.credentials_json)


class CampaignPlan(Base):
    __tablename__ = "campaign_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    advertiser_id: Mapped[int] = mapped_column(ForeignKey("advertisers.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("connections.id"), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)

    budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB", server_default="RUB")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    internal_code: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    advertiser: Mapped["Advertiser"] = relationship(back_populates="plans")
    experiments: Mapped[list["Experiment"]] = relationship(back_populates="plan")
    connection: Mapped["Connection"] = relationship(back_populates="plans")


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("campaign_plans.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    total_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    platforms: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True)
    processing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus, name="experiment_status_enum"), default=ExperimentStatus.draft, nullable=False
    )
    start_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plan: Mapped[CampaignPlan] = relationship(back_populates="experiments")
    creatives: Mapped[list["CreativeVariant"]] = relationship(back_populates="experiment")
    campaigns: Mapped[list["ExperimentCampaign"]] = relationship(back_populates="campaigns")
    builder_campaigns: Mapped[list["BuilderCampaign"]] = relationship(back_populates="experiment")


class ExperimentRound(Base):
    __tablename__ = "experiment_rounds"
    __table_args__ = (UniqueConstraint("experiment_id", "round_index", name="uq_round_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    round_index: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_plan: Mapped[dict] = mapped_column(JSONType, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    experiment: Mapped[Experiment] = relationship()


class HypothesisStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    completed = "done"
    rejected = "rejected"


class Hypothesis(Base):
    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_round_id: Mapped[int] = mapped_column(
        ForeignKey("experiment_rounds.id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    segmentation_params: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    status: Mapped[HypothesisStatus] = mapped_column(
        Enum(HypothesisStatus, name="hypothesis_status_enum"), default=HypothesisStatus.draft, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    experiment_round: Mapped[ExperimentRound] = relationship()


class CreativeVariant(Base):
    __tablename__ = "creative_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    hypothesis_id: Mapped[int | None] = mapped_column(ForeignKey("hypotheses.id"), nullable=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    meta_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    moderation_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_ids: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    compliance_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    experiment: Mapped[Experiment] = relationship(back_populates="creatives")
    hypothesis: Mapped[Hypothesis | None] = relationship()


class ExperimentCampaign(Base):
    __tablename__ = "experiment_campaigns"
    __table_args__ = (
        UniqueConstraint("experiment_id", "platform", "campaign_external_id", name="uq_experiment_campaign"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    campaign_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    experiment: Mapped[Experiment] = relationship(back_populates="campaigns")


class BuilderCampaign(Base):
    __tablename__ = "builder_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), server_default="draft", nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    experiment: Mapped[Experiment] = relationship(back_populates="builder_campaigns")
    ad_groups: Mapped[list["BuilderAdGroup"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")


class BuilderAdGroup(Base):
    __tablename__ = "builder_ad_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("builder_campaigns.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), server_default="draft", nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    campaign: Mapped[BuilderCampaign] = relationship(back_populates="ad_groups")
    ads: Mapped[list["BuilderAd"]] = relationship(back_populates="ad_group", cascade="all, delete-orphan")


class BuilderAd(Base):
    __tablename__ = "builder_ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    ad_group_id: Mapped[int] = mapped_column(ForeignKey("builder_ad_groups.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    utm_json: Mapped[dict] = mapped_column(JSONType, server_default='{}', nullable=False)
    final_url: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    status: Mapped[str] = mapped_column(String(50), server_default="draft", nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    ad_group: Mapped[BuilderAdGroup] = relationship(back_populates="ads")


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    level: Mapped[str] = mapped_column(String, default="campaign", server_default="campaign", nullable=False)
    campaign_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ad_group_external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    ad_external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("campaign_plans.id"), nullable=True)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("connections.id"), nullable=True)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id"), nullable=True)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    spend: Mapped[int] = mapped_column(Integer, default=0)
    leads: Mapped[int] = mapped_column(Integer, default=0)
    purchases: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_metric_snapshots_experiment_platform_date", "experiment_id", "platform", "date"),
        Index("idx_metric_snapshots_campaign", "campaign_external_id"),
        Index("idx_metric_snapshots_connection_date", "connection_id", "date"),
        Index("idx_metric_snapshots_connection_level", "connection_id", "level"),
        Index("idx_metric_snapshots_connection_date_desc", "connection_id", text("date DESC")),
        Index(
            "uq_metric_campaign",
            "organization_id",
            "experiment_id",
            "platform",
            "date",
            "campaign_external_id",
            unique=True,
            postgresql_where=text("level = 'campaign'"),
        ),
        Index(
            "uq_metric_connection_campaign",
            "organization_id",
            "connection_id",
            "platform",
            "date",
            "campaign_external_id",
            unique=True,
            postgresql_where=text("level = 'campaign' AND connection_id IS NOT NULL"),
        ),
        Index(
            "uq_metric_connection_ad_group",
            "organization_id",
            "connection_id",
            "platform",
            "date",
            "campaign_external_id",
            "ad_group_external_id",
            unique=True,
            postgresql_where=text("level = 'ad_group' AND connection_id IS NOT NULL"),
        ),
        Index(
            "uq_metric_connection_ad",
            "organization_id",
            "connection_id",
            "platform",
            "date",
            "campaign_external_id",
            "ad_group_external_id",
            "ad_external_id",
            unique=True,
            postgresql_where=text("level = 'ad' AND connection_id IS NOT NULL"),
        ),
        Index(
            "uq_metric_ad_group",
            "organization_id",
            "experiment_id",
            "platform",
            "date",
            "campaign_external_id",
            "ad_group_external_id",
            unique=True,
            postgresql_where=text("level = 'ad_group'"),
        ),
        Index(
            "uq_metric_ad",
            "organization_id",
            "experiment_id",
            "platform",
            "date",
            "campaign_external_id",
            "ad_group_external_id",
            "ad_external_id",
            unique=True,
            postgresql_where=text("level = 'ad'"),
        ),
    )


class BudgetAllocation(Base):
    __tablename__ = "budget_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    experiment_round_id: Mapped[int | None] = mapped_column(
        ForeignKey("experiment_rounds.id"), nullable=True
    )
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    creative_variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("creative_variants.id"), nullable=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    experiment: Mapped[Experiment] = relationship()
    creative_variant: Mapped[CreativeVariant | None] = relationship()


class ConversionEventType(str, enum.Enum):
    lead = "lead"
    purchase = "purchase"


class ConversionEvent(Base):
    __tablename__ = "conversion_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    event_type: Mapped[ConversionEventType] = mapped_column(Enum(ConversionEventType, name="conversion_event_type_enum"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    landing_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    utm_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_content: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_term: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("campaign_plans.id"), nullable=True)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    plan: Mapped[CampaignPlan | None] = relationship()
    experiment: Mapped[Experiment | None] = relationship()


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    canceled = "canceled"


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("connections.id", ondelete="SET NULL"), nullable=True)
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"), default=JobStatus.pending, nullable=False
    )
    context_json: Mapped[dict] = mapped_column(JSONType, nullable=False, server_default='{}')
    result_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_job_runs_organization_id", "organization_id"),
        Index("idx_job_runs_connection_id", "connection_id"),
        Index("idx_job_runs_status", "status"),
        Index("idx_job_runs_job_type", "job_type"),
        Index("idx_job_runs_created_at_desc", created_at.desc()),
        Index("idx_job_runs_correlation_id", "correlation_id"),
    )


class SyncRunType(str, enum.Enum):
    campaigns = "campaigns"
    metrics = "metrics"
    full = "full"


class SyncRunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"
    canceled = "canceled"


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=True)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("connections.id", ondelete="SET NULL"), nullable=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    run_type: Mapped[SyncRunType] = mapped_column(
        Enum(SyncRunType, name="sync_run_type_enum", native_enum=False), nullable=False
    )
    status: Mapped[SyncRunStatus] = mapped_column(
        Enum(SyncRunStatus, name="sync_run_status_enum", native_enum=False),
        default=SyncRunStatus.queued,
        nullable=False
    )
    params_json: Mapped[dict] = mapped_column(JSONType, nullable=False, server_default='{}')
    result_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    has_warnings: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_sync_runs_experiment_platform_created_at", "experiment_id", "platform", created_at.desc()),
        Index("idx_sync_runs_connection_created_at", "connection_id", created_at.desc()),
        Index("idx_sync_runs_status", "status"),
        Index("idx_sync_runs_correlation_id", "correlation_id"),
    )


class ErirStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    canceled = "canceled"


class ErirToken(Base):
    __tablename__ = "erir_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=True)
    platform: Mapped[Platform | None] = mapped_column(Enum(Platform, name="platform_enum"), nullable=True)
    creative_id: Mapped[int | None] = mapped_column(ForeignKey("ad_creatives.id", ondelete="CASCADE"), nullable=True)
    token: Mapped[str | None] = mapped_column(String, nullable=True)
    token_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_payload_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    response_payload_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    token_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ErirEvent(Base):
    __tablename__ = "erir_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), nullable=True)
    erir_token_id: Mapped[int | None] = mapped_column(ForeignKey("erir_tokens.id", ondelete="CASCADE"), nullable=True)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("connections.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[ErirStatus] = mapped_column(
        Enum(ErirStatus, name="erir_status_enum", native_enum=False),
        default=ErirStatus.pending,
        nullable=False,
    )
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    level: Mapped[str | None] = mapped_column(String(length=20), nullable=True)
    code: Mapped[str | None] = mapped_column(String(length=100), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

# --- Ad Catalog Models ---

class AdCampaign(Base):
    __tablename__ = "ad_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    connection_id: Mapped[int] = mapped_column(ForeignKey("connections.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    desired_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    desired_daily_budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)

    __table_args__ = (
        UniqueConstraint("connection_id", "external_id", name="uq_ad_campaigns"),
        Index("idx_ad_campaigns_org", "organization_id"),
    )


class AdAdGroup(Base):
    __tablename__ = "ad_ad_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    connection_id: Mapped[int] = mapped_column(ForeignKey("connections.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("connection_id", "external_id", name="uq_ad_ad_groups"),
        Index("idx_ad_ad_groups_campaign", "connection_id", "campaign_external_id"),
    )


class AdAd(Base):
    __tablename__ = "ad_ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    connection_id: Mapped[int] = mapped_column(ForeignKey("connections.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    ad_group_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    desired_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("connection_id", "external_id", name="uq_ad_ads"),
        Index("idx_ad_ads_group", "connection_id", "ad_group_external_id"),
    )


class OrgUtmSettings(Base):
    __tablename__ = "org_utm_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    utm_source: Mapped[str] = mapped_column(String(255), server_default="{platform}", nullable=False)
    utm_medium: Mapped[str] = mapped_column(String(255), server_default="cpc", nullable=False)
    utm_campaign_tpl: Mapped[str] = mapped_column(String(255), server_default="{campaign_id}", nullable=False)
    utm_content_tpl: Mapped[str] = mapped_column(String(255), server_default="{ad_id}", nullable=False)
    utm_term_tpl: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_org_utm_settings"),
    )

class OrgRecommendation(Base):
    __tablename__ = "org_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("connections.id", ondelete="CASCADE"), nullable=True)
    subject_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    meta_json: Mapped[dict] = mapped_column(JSONType, nullable=False, server_default='{}')
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "connection_id", "subject_type", "subject_id", "code", "valid_from", "valid_to", name="uq_org_recommendations"),
        Index("idx_org_recommendations_org_created", "organization_id", text("created_at DESC")),
        Index("idx_org_recommendations_conn_created", "organization_id", "connection_id", text("created_at DESC")),
    )

class ChangePlan(Base):
    __tablename__ = "change_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    connection_id: Mapped[int] = mapped_column(ForeignKey("connections.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), server_default="draft", nullable=False)
    date_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_json: Mapped[dict] = mapped_column(JSONType, nullable=False, server_default='{}')

    items: Mapped[list["ChangePlanItem"]] = relationship(back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_change_plans_org_created", "organization_id", text("created_at DESC")),
    )

class ChangePlanItem(Base):
    __tablename__ = "change_plan_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("change_plans.id", ondelete="CASCADE"), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    params_json: Mapped[dict] = mapped_column(JSONType, nullable=False, server_default='{}')
    status: Mapped[str] = mapped_column(String(50), server_default="pending", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    plan: Mapped[ChangePlan] = relationship(back_populates="items")

    __table_args__ = (
        Index("idx_change_plan_items_plan_status", "plan_id", "status"),
    )
