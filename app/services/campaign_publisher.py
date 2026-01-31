"""
Campaign Publisher Service.

Publishes AI-generated creatives to connected ad platforms.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from app.db.models_drafts import DraftCampaign, DraftAdGroup, DraftAd
from app.services.platforms import YandexDirectClient, VKAdsClient, OzonPerformanceClient

logger = logging.getLogger(__name__)


def get_ad_text_with_disclaimer(ad: DraftAd, advertiser_name: str = "Рекламодатель") -> str:
    """
    Get ad text with ERID disclaimer for compliance.
    If ERID is not set, returns original text.
    """
    if ad.erid:
        disclaimer = f"\n\nРеклама. {advertiser_name}. {ad.erid}"
        return (ad.text or "") + disclaimer
    return ad.text or ""


@dataclass
class PublishResult:
    """Result of publishing a campaign."""
    success: bool
    platform: str
    campaign_id: Optional[str] = None
    external_id: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class CampaignPublisher:
    """
    Publishes draft campaigns to external ad platforms.
    
    Workflow:
    1. Get draft campaign with ads
    2. Connect to platform using stored OAuth token
    3. Create campaign structure on platform
    4. Update draft with external IDs
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def publish(
        self,
        draft_campaign_id: int,
        connection_token: str,
    ) -> PublishResult:
        """
        Publish a draft campaign to its target platform.
        
        Args:
            draft_campaign_id: ID of draft campaign to publish
            connection_token: OAuth access token for the platform
        """
        # Get draft campaign
        campaign = self.db.query(DraftCampaign).filter(
            DraftCampaign.id == draft_campaign_id
        ).first()
        
        if not campaign:
            return PublishResult(
                success=False,
                platform="unknown",
                error="Campaign not found",
            )
        
        platform = campaign.platform or "yandex"
        
        try:
            if platform == "yandex":
                return await self._publish_to_yandex(campaign, connection_token)
            elif platform == "vk":
                return await self._publish_to_vk(campaign, connection_token)
            elif platform == "ozon":
                return await self._publish_to_ozon(campaign, connection_token)
            else:
                return PublishResult(
                    success=False,
                    platform=platform,
                    error=f"Unsupported platform: {platform}",
                )
        except Exception as e:
            logger.exception(f"Error publishing to {platform}")
            return PublishResult(
                success=False,
                platform=platform,
                campaign_id=str(draft_campaign_id),
                error=str(e),
            )
    
    async def _publish_to_yandex(
        self,
        campaign: DraftCampaign,
        token: str,
    ) -> PublishResult:
        """Publish campaign to Yandex Direct."""
        client = YandexDirectClient(token)
        
        try:
            # 1. Create campaign
            payload = campaign.payload_json or {}
            budget = payload.get("budget", 1000) * 1000000  # Convert to micro-units
            
            result = await client.create_campaign(
                name=campaign.name,
                daily_budget=budget,
                start_date=datetime.now().strftime("%Y-%m-%d"),
            )
            
            external_campaign_id = result.get("Id")
            if not external_campaign_id:
                return PublishResult(
                    success=False,
                    platform="yandex",
                    campaign_id=str(campaign.id),
                    error="Failed to create campaign",
                    details=result,
                )
            
            # 2. Create ad groups
            ad_groups = self.db.query(DraftAdGroup).filter(
                DraftAdGroup.campaign_id == campaign.id
            ).all()
            
            external_ad_groups = []
            for ag in ad_groups:
                ag_result = await client.create_ad_group(
                    campaign_id=external_campaign_id,
                    name=ag.name,
                )
                external_ad_groups.append({
                    "internal_id": ag.id,
                    "external_id": ag_result.get("Id"),
                })
            
            # 3. Create ads with ERID compliance
            ads_created = 0
            for ag_map in external_ad_groups:
                ads = self.db.query(DraftAd).filter(
                    DraftAd.ad_group_id == ag_map["internal_id"]
                ).all()
                
                for ad in ads:
                    # Note: Yandex Direct has separate field for ERID (erid parameter in API)
                    # For now we pass text as-is, ERID stored for reporting
                    await client.create_text_ad(
                        ad_group_id=ag_map["external_id"],
                        title=ad.title[:35],
                        text=ad.text[:81],
                        href=ad.landing_url or campaign.payload_json.get("landing_url", ""),
                        # erid=ad.erid  # TODO: Add when Yandex API client supports it
                    )
                    ads_created += 1
            
            # 4. Add keywords if available
            keywords = payload.get("keywords", [])
            if keywords and external_ad_groups:
                await client.add_keywords(
                    ad_group_id=external_ad_groups[0]["external_id"],
                    keywords=keywords[:200],  # Yandex limit
                )
            
            # 5. Update draft campaign status
            campaign.status = "published"
            campaign.payload_json = {
                **(campaign.payload_json or {}),
                "external_id": external_campaign_id,
                "published_at": datetime.utcnow().isoformat(),
            }
            self.db.commit()
            
            return PublishResult(
                success=True,
                platform="yandex",
                campaign_id=str(campaign.id),
                external_id=str(external_campaign_id),
                details={
                    "ad_groups_created": len(external_ad_groups),
                    "ads_created": ads_created,
                    "keywords_added": len(keywords),
                },
            )
            
        finally:
            await client.close()
    
    async def _publish_to_vk(
        self,
        campaign: DraftCampaign,
        token: str,
    ) -> PublishResult:
        """Publish campaign to VK Ads."""
        client = VKAdsClient(token)
        
        try:
            # Get account ID (use first available)
            accounts = await client.get_accounts()
            if not accounts:
                return PublishResult(
                    success=False,
                    platform="vk",
                    campaign_id=str(campaign.id),
                    error="No VK Ads accounts found",
                )
            
            account_id = accounts[0]["id"]
            payload = campaign.payload_json or {}
            budget = payload.get("budget", 1000) * 100  # Convert to kopecks
            
            # 1. Create campaign
            result = await client.create_campaign(
                account_id=account_id,
                name=campaign.name,
                objective="traffic",
                budget_limit_day=budget,
            )
            
            external_campaign_id = result.get("id")
            if not external_campaign_id:
                return PublishResult(
                    success=False,
                    platform="vk",
                    campaign_id=str(campaign.id),
                    error="Failed to create campaign",
                    details=result,
                )
            
            # 2. Create ad group
            package = await client.create_ad_group(
                campaign_id=external_campaign_id,
                name="Основная группа",
            )
            package_id = package.get("id")
            
            # 3. Create ads
            ads_created = 0
            ads = self.db.query(DraftAd).join(DraftAdGroup).filter(
                DraftAdGroup.campaign_id == campaign.id
            ).all()
            
            landing_url = payload.get("landing_url", "")
            for ad in ads[:10]:  # VK limit per group
                await client.create_ad(
                    package_id=package_id,
                    title=ad.title[:33],
                    description=ad.text[:220],
                    link_url=ad.landing_url or landing_url,
                )
                ads_created += 1
            
            # 4. Update draft
            campaign.status = "published"
            campaign.payload_json = {
                **(campaign.payload_json or {}),
                "external_id": external_campaign_id,
                "vk_account_id": account_id,
                "published_at": datetime.utcnow().isoformat(),
            }
            self.db.commit()
            
            return PublishResult(
                success=True,
                platform="vk",
                campaign_id=str(campaign.id),
                external_id=str(external_campaign_id),
                details={
                    "account_id": account_id,
                    "ad_groups_created": 1,
                    "ads_created": ads_created,
                },
            )
            
        finally:
            await client.close()
    
    async def _publish_to_ozon(
        self,
        campaign: DraftCampaign,
        token: str,
    ) -> PublishResult:
        """Publish campaign to Ozon Performance."""
        client = OzonPerformanceClient(token)
        
        try:
            payload = campaign.payload_json or {}
            budget = payload.get("budget", 500)
            
            # Get product IDs from payload
            product_ids = payload.get("product_ids", [])
            if not product_ids:
                return PublishResult(
                    success=False,
                    platform="ozon",
                    campaign_id=str(campaign.id),
                    error="No product IDs specified for Ozon campaign",
                )
            
            # 1. Create CPC campaign
            result = await client.create_cpc_campaign(
                title=campaign.name,
                product_ids=product_ids,
                daily_budget=budget,
                placement="PLACEMENT_SEARCH_AND_CATEGORY",
            )
            
            external_campaign_id = result.get("campaignId")
            if not external_campaign_id:
                return PublishResult(
                    success=False,
                    platform="ozon",
                    campaign_id=str(campaign.id),
                    error="Failed to create campaign",
                    details=result,
                )
            
            # 2. Activate campaign
            await client.activate_campaign(external_campaign_id)
            
            # 3. Update draft
            campaign.status = "published"
            campaign.payload_json = {
                **(campaign.payload_json or {}),
                "external_id": external_campaign_id,
                "published_at": datetime.utcnow().isoformat(),
            }
            self.db.commit()
            
            return PublishResult(
                success=True,
                platform="ozon",
                campaign_id=str(campaign.id),
                external_id=str(external_campaign_id),
                details={
                    "products_count": len(product_ids),
                    "daily_budget": budget,
                },
            )
            
        finally:
            await client.close()
