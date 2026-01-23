from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class MagicRunCreate(BaseModel):
    landing_url: Optional[str] = None
    description: Optional[str] = None
    platform: str = "yandex"
    campaign_goal: Optional[str] = None
    target_audience: Optional[str] = None
    budget_total: Optional[float] = None
    budget_daily: Optional[float] = None
    ad_count: Optional[int] = Field(default=9, ge=1, le=20)
    connection_id: Optional[int] = None
    connection_ids: Optional[List[int]] = None
    product_ids: Optional[List[int]] = None

class MagicRunResponse(BaseModel):
    id: int
    organization_id: int
    status: str
    input_json: Optional[Dict[str, Any]]
    result_json: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MagicLaunchRequest(BaseModel):
    total_budget: int = 15000
    platforms: List[str] = ["yandex"]
