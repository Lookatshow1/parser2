import enum
from decimal import Decimal
from datetime import datetime, date

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Platform(str, enum.Enum):
    yandex = "yandex"
    ozon = "ozon"
    vk = "vk"


class ConnectionStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    error = "error"


class ExperimentStatus(str, enum.Enum):
    planned = "draft"
    running = "running"
    stopped = "stopped"
    completed = "completed"


class Advertiser(Base):
    __tablename__ = "advertisers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    connections: Mapped[list["Connection"]] = relationship(back_populates="advertiser")
    plans: Mapped[list["CampaignPlan"]] = relationship(back_populates="advertiser")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    advertiser_id: Mapped[int | None] = mapped_column(ForeignKey("advertisers.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    advertiser: Mapped[Advertiser | None] = relationship()


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    advertiser_id: Mapped[int | None] = mapped_column(ForeignKey("advertisers.id"), nullable=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    credentials_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus, name="connection_status_enum"), default=ConnectionStatus.active, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    advertiser: Mapped[Advertiser | None] = relationship(back_populates="connections")


class CampaignPlan(Base):
    __tablename__ = "campaign_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    advertiser_id: Mapped[int] = mapped_column(ForeignKey("advertisers.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)

    budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    internal_code: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    advertiser: Mapped["Advertiser"] = relationship(back_populates="plans")
    experiments: Mapped[list["Experiment"]] = relationship(back_populates="plan")


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("campaign_plans.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    total_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    platforms: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    processing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus, name="experiment_status_enum"), default=ExperimentStatus.planned, nullable=False
    )
    start_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plan: Mapped[CampaignPlan] = relationship(back_populates="experiments")
    creatives: Mapped[list["CreativeVariant"]] = relationship(back_populates="experiment")


class ExperimentRound(Base):
    __tablename__ = "experiment_rounds"
    __table_args__ = (UniqueConstraint("experiment_id", "round_index", name="uq_round_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    round_index: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_plan: Mapped[dict] = mapped_column(JSONB, nullable=False)
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
    segmentation_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
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
    meta_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    moderation_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    external_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    compliance_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    experiment: Mapped[Experiment] = relationship(back_populates="creatives")
    hypothesis: Mapped[Hypothesis | None] = relationship()


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, name="platform_enum"), nullable=False)
    campaign_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    spend: Mapped[int] = mapped_column(Integer, default=0)
    leads: Mapped[int] = mapped_column(Integer, default=0)
    purchases: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plan: Mapped[CampaignPlan | None] = relationship()
    experiment: Mapped[Experiment | None] = relationship()
