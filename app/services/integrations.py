from typing import Dict, Type
from app.adapters.platforms.base import PlatformAdapter
from app.adapters.platforms.yandex_mock import YandexMockAdapter
from app.db.models_drafts import DraftCampaign
from sqlalchemy.orm import Session
from datetime import datetime

class IntegrationService:
    def __init__(self, db: Session):
        self.db = db
        self._adapters: Dict[str, Type[PlatformAdapter]] = {
            "yandex": YandexMockAdapter,
            # "google": GoogleAdWordsAdapter, # Future
        }

    def get_adapter(self, platform: str) -> PlatformAdapter:
        adapter_cls = self._adapters.get(platform.lower())
        if not adapter_cls:
            raise ValueError(f"Platform {platform} not supported")
        return adapter_cls()

    async def publish_draft(self, draft_id: int):
        draft = self.db.query(DraftCampaign).filter(DraftCampaign.id == draft_id).first()
        if not draft:
            raise ValueError("Draft not found")

        adapter = self.get_adapter(draft.platform)
        
        # Apply UTM tags to all ads
        self._apply_utms(draft)
        
        # In a real system, we'd recursively convert DraftAdGroups -> Platform Format
        # Here we just mock the campaign creation call
        external_id = await adapter.publish_campaign(draft)
        
        draft.status = "published"
        draft.payload_json = {**(draft.payload_json or {}), "external_id": external_id}
        draft.updated_at = datetime.utcnow()
        self.db.commit()
        
        return external_id

    def _apply_utms(self, campaign: DraftCampaign):
        import urllib.parse
        
        for group in campaign.ad_groups:
            for ad in group.ads:
                if not ad.landing_url:
                    continue
                    
                # Basic UTM Construction
                params = {
                    "utm_source": campaign.platform,
                    "utm_medium": "cpc",
                    "utm_campaign": f"{campaign.id}-{urllib.parse.quote(campaign.name)}",
                    "utm_content": str(ad.id)
                }
                
                url_parts = list(urllib.parse.urlparse(ad.landing_url))
                query = dict(urllib.parse.parse_qsl(url_parts[4]))
                query.update(params)
                
                url_parts[4] = urllib.parse.urlencode(query)
                ad.final_url = urllib.parse.urlunparse(url_parts)


    async def import_campaigns_to_drafts(self, platform: str, account_id: str, org_id: int):
        adapter = self.get_adapter(platform)
        campaigns_data = await adapter.fetch_campaigns(account_id)
        
        created_drafts = []
        for c_data in campaigns_data:
            # Create a draft from the imported data
            draft = DraftCampaign(
                organization_id=org_id,
                name=f"[Import] {c_data['name']}",
                platform=platform,
                status="draft",
                payload_json=c_data
            )
            self.db.add(draft)
            self.db.commit()
            created_drafts.append(draft)
            
        return created_drafts

    async def import_campaigns(self, platform: str, account_id: str, org_id: int):
        adapter = self.get_adapter(platform)
        campaigns_data = await adapter.fetch_campaigns(account_id)
        
        created_drafts = []
        for c_data in campaigns_data:
            draft = DraftCampaign(
                organization_id=org_id,
                name=f"[Import] {c_data['name']}",
                platform=platform,
                status="draft",
                payload_json=c_data
            )
            self.db.add(draft)
            self.db.commit()
            created_drafts.append(draft)
            
        return created_drafts

