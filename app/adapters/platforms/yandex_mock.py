from typing import List, Dict, Any
from app.adapters.platforms.base import PlatformAdapter
import uuid
import random
import asyncio

class YandexMockAdapter(PlatformAdapter):
    
    async def fetch_campaigns(self, account_id: str) -> List[Dict[str, Any]]:
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        # Deterministic mock data
        return [
            {"id": "ya_c_101", "name": "Search - Brands - Mock", "status": "active", "budget": 1500},
            {"id": "ya_c_102", "name": "Network - Retargeting - Mock", "status": "paused", "budget": 500}
        ]

    async def fetch_ad_groups(self, campaign_id: str) -> List[Dict[str, Any]]:
        await asyncio.sleep(0.3)
        return [
            {"id": f"ya_g_{campaign_id}_1", "name": "Group A", "status": "active"},
            {"id": f"ya_g_{campaign_id}_2", "name": "Group B", "status": "active"}
        ]
    
    async def fetch_ads(self, group_id: str) -> List[Dict[str, Any]]:
        await asyncio.sleep(0.2)
        return [
            {"id": f"ya_a_{group_id}_1", "title": "Buy Now", "text": "Best Product Ever", "url": "https://example.com"}
        ]

    async def publish_campaign(self, draft_campaign: Any) -> str:
        """
        Simulates publishing a campaign.
        Expects draft_campaign to be a DraftCampaign model or dict.
        """
        await asyncio.sleep(1.5) # Simulate long API call
        
        external_id = f"ya_new_{uuid.uuid4().hex[:8]}"
        return external_id
