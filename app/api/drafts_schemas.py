from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class DraftAdBase(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    landing_url: Optional[str] = None
    payload_json: Optional[Dict[str, Any]] = {}

class DraftAdCreate(DraftAdBase):
    ad_group_id: int

class DraftAdUpdate(DraftAdBase):
    pass

class DraftAdResponse(DraftAdBase):
    id: int
    ad_group_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class DraftAdGroupBase(BaseModel):
    name: str
    payload_json: Optional[Dict[str, Any]] = {}

class DraftAdGroupCreate(DraftAdGroupBase):
    campaign_id: int

class DraftAdGroupResponse(DraftAdGroupBase):
    id: int
    campaign_id: int
    ads: List[DraftAdResponse] = []
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class DraftCampaignBase(BaseModel):
    name: str
    platform: str = "yandex"
    status: str = "draft"
    payload_json: Optional[Dict[str, Any]] = {}

class DraftCampaignCreate(DraftCampaignBase):
    pass

class DraftCampaignResponse(DraftCampaignBase):
    id: int
    organization_id: int
    magic_run_id: Optional[int]
    ad_groups: List[DraftAdGroupResponse] = []
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
