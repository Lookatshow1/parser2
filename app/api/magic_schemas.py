from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class MagicRunCreate(BaseModel):
    landing_url: str
    description: Optional[str] = None
    platform: str = "yandex"
    campaign_goal: Optional[str] = None
    target_audience: Optional[str] = None
    budget_total: Optional[float] = None

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
