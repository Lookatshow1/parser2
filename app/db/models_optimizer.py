"""
Budget Optimizer Models

Models for AI-powered budget allocation and optimization rules.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON, Boolean, Text
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class OptimizationRuleType(str, enum.Enum):
    PAUSE_LOW_CTR = "pause_low_ctr"
    INCREASE_HIGH_ROAS = "increase_high_roas"
    DECREASE_LOW_ROAS = "decrease_low_roas"
    DAYPARTING = "dayparting"
    BUDGET_CAP = "budget_cap"


class BudgetAllocation(Base):
    """Recommended or applied budget allocation."""
    __tablename__ = "budget_allocations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Allocation details
    campaign_id = Column(Integer, nullable=True)
    campaign_name = Column(String(255), nullable=True)
    platform = Column(String(50), nullable=False)
    
    # Budget values
    current_budget = Column(Float, default=0.0)
    recommended_budget = Column(Float, default=0.0)
    change_percentage = Column(Float, default=0.0)
    
    # Reasoning
    reason = Column(Text, nullable=True)
    expected_roas_improvement = Column(Float, nullable=True)
    
    # Status
    status = Column(String(50), default="pending")  # pending, applied, rejected
    applied_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization")


class OptimizationRule(Base):
    """Automated optimization rule."""
    __tablename__ = "optimization_rules"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False)
    
    # Rule conditions (JSON for flexibility)
    conditions = Column(JSON, default=lambda: {})
    # Example: {"metric": "ctr", "operator": "<", "value": 0.5}
    
    # Rule actions (JSON)
    actions = Column(JSON, default=lambda: {})
    # Example: {"action": "decrease_budget", "percentage": 20}
    
    # Scope
    platform = Column(String(50), nullable=True)  # null = all platforms
    campaign_ids = Column(JSON, nullable=True)  # null = all campaigns
    
    # Status
    is_enabled = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization")


class OptimizationLog(Base):
    """Log of optimization actions taken."""
    __tablename__ = "optimization_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("optimization_rules.id"), nullable=True)
    
    action_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    
    # What was affected
    campaign_id = Column(Integer, nullable=True)
    campaign_name = Column(String(255), nullable=True)
    platform = Column(String(50), nullable=True)
    
    # Before/After
    before_value = Column(Float, nullable=True)
    after_value = Column(Float, nullable=True)
    
    # Outcome
    status = Column(String(50), default="executed")  # executed, failed, rolled_back
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization")
    rule = relationship("OptimizationRule")
