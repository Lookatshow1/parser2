import enum
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class DraftStatus(str, enum.Enum):
    draft = "draft"
    ready = "ready"
    published = "published"
    failed = "failed"

class DraftCampaign(Base):
    __tablename__ = "draft_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("connections.id", ondelete="SET NULL"), nullable=True)
    magic_run_id: Mapped[int | None] = mapped_column(ForeignKey("magic_runs.id", ondelete="SET NULL"), nullable=True)
    
    platform: Mapped[str] = mapped_column(String, nullable=False) # yandex, vk, etc.
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[DraftStatus] = mapped_column(String, default=DraftStatus.draft, nullable=False)
    
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # Platform specific payload
    validation_errors_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    ad_groups = relationship("DraftAdGroup", back_populates="campaign", cascade="all, delete-orphan")
    organization = relationship("Organization")
    connection = relationship("Connection")
    magic_run = relationship("MagicRun")


class DraftAdGroup(Base):
    __tablename__ = "draft_ad_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("draft_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validation_errors_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    campaign = relationship("DraftCampaign", back_populates="ad_groups")
    ads = relationship("DraftAd", back_populates="ad_group", cascade="all, delete-orphan")


class DraftAd(Base):
    __tablename__ = "draft_ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad_group_id: Mapped[int] = mapped_column(ForeignKey("draft_ad_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    landing_url: Mapped[str | None] = mapped_column(String, nullable=True)
    final_url: Mapped[str | None] = mapped_column(String, nullable=True) # UTM calculated

    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validation_errors_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    ad_group = relationship("DraftAdGroup", back_populates="ads")
