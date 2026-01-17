"""
A/B Testing API Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class VariantCreate(BaseModel):
    name: str
    title: Optional[str] = None
    text: Optional[str] = None
    landing_url: Optional[str] = None
    draft_ad_id: Optional[int] = None


class ABTestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    variants: List[VariantCreate]
    primary_metric: str = "ctr"
    min_sample_size: int = 1000
    confidence_level: float = 0.95


class VariantResponse(BaseModel):
    id: int
    name: str
    title: Optional[str]
    text: Optional[str]
    landing_url: Optional[str]
    traffic_percentage: int
    impressions: int
    clicks: int
    conversions: int
    spend: float
    revenue: float
    ctr: float
    conversion_rate: float
    cpc: float
    roas: float

    class Config:
        from_attributes = True


class ABTestResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    primary_metric: str
    min_sample_size: int
    confidence_level: float
    winner_variant_id: Optional[int]
    statistical_significance: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    variants: List[VariantResponse] = []

    class Config:
        from_attributes = True


class SignificanceResponse(BaseModel):
    significant: bool
    p_value: Optional[float]
    chi2: Optional[float]
    confidence: Optional[float]
    winner_id: Optional[int]
    winner_name: Optional[str]
    variant_a: Optional[dict]
    variant_b: Optional[dict]
    reason: Optional[str]


class MetricsUpdate(BaseModel):
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0
