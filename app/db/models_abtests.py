"""
A/B Testing Models

Models for managing A/B tests on ad campaigns.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class ABTestStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    WINNER_SELECTED = "winner_selected"


class ABTest(Base):
    """A/B test comparing multiple ad variants."""
    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Test configuration
    status = Column(String(50), default=ABTestStatus.DRAFT.value)
    traffic_split = Column(JSON, default=lambda: {})  # {"variant_a": 50, "variant_b": 50}
    
    # Success metrics
    primary_metric = Column(String(50), default="ctr")  # ctr, conversions, roas
    min_sample_size = Column(Integer, default=1000)
    confidence_level = Column(Float, default=0.95)  # 95% confidence
    
    # Results
    winner_variant_id = Column(Integer, ForeignKey("ab_test_variants.id"), nullable=True)
    statistical_significance = Column(Float, nullable=True)  # p-value
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    # Relationships
    variants = relationship("ABTestVariant", back_populates="ab_test", foreign_keys="ABTestVariant.ab_test_id")
    organization = relationship("Organization")


class ABTestVariant(Base):
    """A variant in an A/B test (e.g., different ad copy)."""
    __tablename__ = "ab_test_variants"

    id = Column(Integer, primary_key=True, index=True)
    ab_test_id = Column(Integer, ForeignKey("ab_tests.id"), nullable=False)
    name = Column(String(100), nullable=False)  # "Variant A", "Variant B"
    
    # The ad being tested
    draft_ad_id = Column(Integer, ForeignKey("draft_ads.id"), nullable=True)
    
    # Ad content (can be custom or from draft)
    title = Column(String(255), nullable=True)
    text = Column(Text, nullable=True)
    landing_url = Column(String(2048), nullable=True)
    
    # Traffic allocation percentage
    traffic_percentage = Column(Integer, default=50)

    # Link to real campaign for metrics
    campaign_external_id = Column(String(255), nullable=True)
    
    # Metrics collected
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)
    
    # Calculated metrics (updated periodically)
    ctr = Column(Float, default=0.0)  # clicks / impressions
    conversion_rate = Column(Float, default=0.0)  # conversions / clicks
    cpc = Column(Float, default=0.0)  # spend / clicks
    roas = Column(Float, default=0.0)  # revenue / spend
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ab_test = relationship("ABTest", back_populates="variants", foreign_keys=[ab_test_id])
    draft_ad = relationship("DraftAd")


class ABTestResult(Base):
    """Daily snapshot of A/B test results."""
    __tablename__ = "ab_test_results"

    id = Column(Integer, primary_key=True, index=True)
    ab_test_id = Column(Integer, ForeignKey("ab_tests.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("ab_test_variants.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Daily metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ab_test = relationship("ABTest")
    variant = relationship("ABTestVariant")
