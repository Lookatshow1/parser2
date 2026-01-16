from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class PlatformAdapter(ABC):
    
    @abstractmethod
    async def fetch_campaigns(self, account_id: str) -> List[Dict[str, Any]]:
        """Fetch list of campaigns from the platform."""
        pass

    @abstractmethod
    async def fetch_ad_groups(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Fetch list of ad groups for a campaign."""
        pass
    
    @abstractmethod
    async def fetch_ads(self, group_id: str) -> List[Dict[str, Any]]:
        """Fetch list of ads for an ad group."""
        pass

    @abstractmethod
    async def publish_campaign(self, draft_campaign: Any) -> str:
        """Publish a draft campaign to the platform. Returns external ID."""
        pass
