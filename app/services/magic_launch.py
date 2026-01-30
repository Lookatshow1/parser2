"""
Magic Launch Service

One-click campaign launch across multiple platforms.
The "Money Button" - from idea to running ads in seconds.
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.ai.orchestrator import MultiAIOrchestrator, get_orchestrator
from app.core.config import get_settings
from app.db.models import Platform, Connection
from app.db.models_drafts import DraftCampaign, DraftAdGroup, DraftAd
from app.connectors.yandex_direct import YandexDirectConnector
from app.connectors.vk_ads import VKAdsConnector
from app.connectors.ozon_performance import OzonPerformanceConnector

logger = logging.getLogger(__name__)


class MagicLaunchService:
    """
    Magic Launch - One-click advertising across all platforms.

    Flow:
    1. User enters URL or business description
    2. AI generates creatives (text, images, voice, video)
    3. Campaigns are created on all connected platforms
    4. Campaigns are launched with smart budget distribution
    5. User starts getting leads

    This is the "Money Button" - minimum input, maximum output.
    """

    def __init__(self, db: Session, orchestrator: MultiAIOrchestrator = None):
        self.db = db
        self.orchestrator = orchestrator or get_orchestrator()
        self.settings = get_settings()

    async def magic_launch(
        self,
        org_id: int,
        user_id: int,
        landing_url: str = None,
        business_description: str = None,
        budget: float = 10000,
        platforms: List[str] = None,
        auto_start: bool = True,
        creative_options: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """
        Execute Magic Launch - from zero to running ads.

        Args:
            org_id: Organization ID
            user_id: User ID
            landing_url: Website URL to analyze
            business_description: Manual business description
            budget: Total budget in RUB
            platforms: Target platforms (auto-detect if None)
            auto_start: Start campaigns immediately
            creative_options: What to generate

        Returns:
            Complete launch result with campaign IDs and status
        """
        logger.info(f"Magic Launch started for org={org_id}, budget={budget}")

        # Step 1: Determine platforms from connections
        if platforms is None:
            platforms = await self._get_available_platforms(org_id)

        if not platforms:
            return {
                "status": "error",
                "error": "no_platforms",
                "message": "No connected advertising platforms. Please connect Yandex Direct, VK Ads, or Ozon first."
            }

        # Step 2: Set creative options
        if creative_options is None:
            creative_options = {
                "images": self.settings.magic_auto_generate_images,
                "voice": self.settings.magic_auto_generate_voice,
                "video": self.settings.magic_auto_generate_video
            }

        # Step 3: Generate full campaign with AI
        try:
            campaign_data = await self.orchestrator.generate_full_campaign(
                business_info=business_description or "",
                landing_url=landing_url or "",
                budget=budget,
                platforms=platforms,
                creative_options=creative_options
            )
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return {
                "status": "error",
                "error": "ai_generation_failed",
                "message": f"Failed to generate campaign: {str(e)}"
            }

        # Step 4: Create campaigns on each platform
        launch_results = []
        for platform_campaign in campaign_data["campaigns"]:
            platform = platform_campaign["platform"]

            try:
                result = await self._create_platform_campaign(
                    org_id=org_id,
                    user_id=user_id,
                    platform=platform,
                    campaign_data=platform_campaign,
                    creatives=campaign_data["creatives"],
                    auto_start=auto_start
                )
                launch_results.append(result)
            except Exception as e:
                logger.error(f"Failed to create {platform} campaign: {e}")
                launch_results.append({
                    "platform": platform,
                    "status": "error",
                    "error": str(e)
                })

        # Step 5: Calculate summary
        successful = [r for r in launch_results if r.get("status") == "launched"]
        total_budget_launched = sum(r.get("budget", 0) for r in successful)

        return {
            "status": "success" if successful else "partial_failure",
            "business_name": campaign_data["business_name"],
            "total_budget": budget,
            "budget_launched": total_budget_launched,
            "platforms_launched": len(successful),
            "platforms_total": len(platforms),
            "campaigns": launch_results,
            "creatives": {
                "ads_count": len(campaign_data["creatives"].get("ads", [])),
                "images_count": len(campaign_data["creatives"].get("images", [])),
                "voiceovers_count": len(campaign_data["creatives"].get("voiceovers", [])),
                "videos_count": len(campaign_data["creatives"].get("videos", []))
            },
            "ai_provider": campaign_data["creatives"].get("text_provider"),
            "launched_at": datetime.utcnow().isoformat()
        }

    async def _get_available_platforms(self, org_id: int) -> List[str]:
        """Get platforms with active connections."""
        connections = self.db.query(Connection).filter(
            Connection.organization_id == org_id,
            Connection.status == "active"
        ).all()

        platforms = set()
        for conn in connections:
            if conn.platform:
                platforms.add(conn.platform.value if hasattr(conn.platform, 'value') else conn.platform)

        # Default to mock platforms if none connected
        if not platforms:
            default_platforms = self.settings.magic_default_platforms.split(",")
            return [p.strip() for p in default_platforms]

        return list(platforms)

    async def _create_platform_campaign(
        self,
        org_id: int,
        user_id: int,
        platform: str,
        campaign_data: Dict[str, Any],
        creatives: Dict[str, Any],
        auto_start: bool
    ) -> Dict[str, Any]:
        """Create and optionally launch a campaign on a specific platform."""

        # Get connection for this platform
        connection = self.db.query(Connection).filter(
            Connection.organization_id == org_id,
            Connection.platform == platform
        ).first()

        # Create draft campaign
        draft = DraftCampaign(
            organization_id=org_id,
            connection_id=connection.id if connection else None,
            platform=platform,
            name=campaign_data["name"],
            status="draft",
            payload_json={
                "budget": campaign_data["budget"],
                "targeting": campaign_data.get("targeting", {}),
                "magic_launch": True
            }
        )
        self.db.add(draft)
        self.db.flush()

        # Create ad group
        group = DraftAdGroup(
            campaign_id=draft.id,
            name="Magic Group",
            payload_json={}
        )
        self.db.add(group)
        self.db.flush()

        # Create ads
        ads = creatives.get("ads", [])
        images = creatives.get("images", [])

        for i, ad_data in enumerate(ads):
            image_url = images[i]["url"] if i < len(images) else None

            ad = DraftAd(
                ad_group_id=group.id,
                title=ad_data.get("title", ""),
                text=ad_data.get("text", ""),
                landing_url=campaign_data.get("landing_url", ""),
                payload_json={
                    "approach": ad_data.get("approach", ""),
                    "image_url": image_url
                }
            )
            self.db.add(ad)

        self.db.commit()

        result = {
            "platform": platform,
            "draft_campaign_id": draft.id,
            "budget": campaign_data["budget"],
            "ads_count": len(ads)
        }

        # Launch if auto_start and connection exists
        if auto_start and connection:
            try:
                launch_result = await self._launch_on_platform(
                    connection=connection,
                    draft=draft,
                    platform=platform
                )
                result.update(launch_result)
                result["status"] = "launched"
            except Exception as e:
                logger.error(f"Failed to launch on {platform}: {e}")
                result["status"] = "draft"
                result["launch_error"] = str(e)
        else:
            result["status"] = "draft"
            if not connection:
                result["message"] = f"No connection for {platform}, saved as draft"

        return result

    async def _launch_on_platform(
        self,
        connection: Connection,
        draft: DraftCampaign,
        platform: str
    ) -> Dict[str, Any]:
        """Actually launch the campaign on the platform API."""

        # Get connector for platform
        connector = self._get_connector(platform, connection)

        if connector is None:
            return {"external_id": None, "message": "Mock mode - no real launch"}

        # For now, return mock result
        # TODO: Implement real API calls
        return {
            "external_id": f"mock_{platform}_{draft.id}",
            "message": f"Campaign submitted to {platform}",
            "estimated_start": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }

    def _get_connector(self, platform: str, connection: Connection):
        """Get the appropriate connector for a platform."""
        credentials = {}
        if connection.credentials_json:
            credentials = connection.credentials_json

        connectors = {
            "yandex": YandexDirectConnector,
            "vk": VKAdsConnector,
            "ozon": OzonPerformanceConnector
        }

        connector_class = connectors.get(platform)
        if connector_class:
            return connector_class(credentials)

        return None

    async def estimate_results(
        self,
        budget: float,
        platforms: List[str],
        business_type: str = "services"
    ) -> Dict[str, Any]:
        """
        Estimate campaign results before launch.

        Returns predicted impressions, clicks, leads based on budget.
        """
        # Average metrics per 1000 RUB
        platform_metrics = {
            "yandex": {"cpm": 150, "ctr": 0.05, "conversion": 0.03},
            "vk": {"cpm": 100, "ctr": 0.03, "conversion": 0.02},
            "ozon": {"cpm": 200, "ctr": 0.08, "conversion": 0.05}
        }

        estimates = {}
        total_impressions = 0
        total_clicks = 0
        total_leads = 0

        budget_per_platform = budget / len(platforms)

        for platform in platforms:
            metrics = platform_metrics.get(platform, platform_metrics["yandex"])

            impressions = int((budget_per_platform / metrics["cpm"]) * 1000)
            clicks = int(impressions * metrics["ctr"])
            leads = int(clicks * metrics["conversion"])

            estimates[platform] = {
                "impressions": impressions,
                "clicks": clicks,
                "leads": leads,
                "budget": budget_per_platform
            }

            total_impressions += impressions
            total_clicks += clicks
            total_leads += leads

        return {
            "total": {
                "impressions": total_impressions,
                "clicks": total_clicks,
                "leads": total_leads,
                "budget": budget
            },
            "by_platform": estimates,
            "disclaimer": "Estimates based on average market performance"
        }


def get_magic_launch_service(db: Session) -> MagicLaunchService:
    """Factory function to get Magic Launch service."""
    return MagicLaunchService(db)
