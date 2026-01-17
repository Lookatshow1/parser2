"""
Analytics Models

Models for storing and aggregating campaign metrics.
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Date, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class CampaignMetrics(Base):
    """Daily aggregated metrics for campaigns."""
    __tablename__ = "campaign_metrics"
    
    __table_args__ = (
        Index("ix_campaign_metrics_date_campaign", "date", "campaign_id"),
        Index("ix_campaign_metrics_org_date", "organization_id", "date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    campaign_id = Column(Integer, nullable=True)  # External campaign ID
    platform = Column(String(50), nullable=False)  # yandex, google, vk
    date = Column(Date, nullable=False)
    
    # Traffic metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    
    # Cost metrics
    spend = Column(Float, default=0.0)
    
    # Conversion metrics
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    
    # Calculated metrics (denormalized for performance)
    ctr = Column(Float, default=0.0)  # clicks / impressions * 100
    cpc = Column(Float, default=0.0)  # spend / clicks
    cpm = Column(Float, default=0.0)  # spend / impressions * 1000
    conversion_rate = Column(Float, default=0.0)  # conversions / clicks * 100
    cpa = Column(Float, default=0.0)  # spend / conversions
    roas = Column(Float, default=0.0)  # revenue / spend
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization")


class AggregatedMetrics(Base):
    """Weekly/Monthly aggregated metrics for faster dashboard loading."""
    __tablename__ = "aggregated_metrics"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    period_type = Column(String(10), nullable=False)  # weekly, monthly
    period_start = Column(Date, nullable=False)
    platform = Column(String(50), nullable=True)  # null = all platforms
    
    # Aggregated metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Float, default=0.0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    
    # Calculated
    ctr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)
    roas = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
