"""
Multi-AI Orchestrator

Intelligent orchestration of multiple AI providers for best results.
Combines text, image, voice, and video generation into a seamless pipeline.
"""
import os
import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass

from app.core.ai.interfaces import TextProvider, ImageProvider
from app.core.ai.openrouter_provider import OpenRouterProvider, OpenRouterImageProvider
from app.core.ai.gigachat_provider import GigaChatProvider
from app.core.ai.elevenlabs_provider import ElevenLabsProvider
from app.core.ai.heygen_provider import HeyGenProvider

logger = logging.getLogger(__name__)


class AITask(Enum):
    """Types of AI tasks."""
    TEXT_GENERATION = "text"
    IMAGE_GENERATION = "image"
    VOICE_GENERATION = "voice"
    VIDEO_GENERATION = "video"
    AD_CREATIVE = "ad_creative"
    FULL_CAMPAIGN = "full_campaign"


@dataclass
class AIProviderConfig:
    """Configuration for an AI provider."""
    name: str
    priority: int  # Lower = higher priority
    cost_per_1k: float  # Cost per 1000 tokens/units
    speed_rating: int  # 1-10, higher = faster
    quality_rating: int  # 1-10, higher = better
    supports_russian: bool
    requires_proxy: bool


# Provider configurations
PROVIDER_CONFIGS = {
    "gigachat": AIProviderConfig(
        name="GigaChat",
        priority=1,
        cost_per_1k=0.001,
        speed_rating=8,
        quality_rating=7,
        supports_russian=True,
        requires_proxy=False
    ),
    "openrouter_gpt4o": AIProviderConfig(
        name="GPT-4o via OpenRouter",
        priority=2,
        cost_per_1k=0.01,
        speed_rating=7,
        quality_rating=9,
        supports_russian=True,
        requires_proxy=True
    ),
    "openrouter_claude": AIProviderConfig(
        name="Claude via OpenRouter",
        priority=3,
        cost_per_1k=0.015,
        speed_rating=6,
        quality_rating=10,
        supports_russian=True,
        requires_proxy=True
    ),
    "openrouter_mixtral": AIProviderConfig(
        name="Mixtral via OpenRouter",
        priority=4,
        cost_per_1k=0.0006,
        speed_rating=9,
        quality_rating=7,
        supports_russian=True,
        requires_proxy=True
    ),
}


class MultiAIOrchestrator:
    """
    Orchestrates multiple AI providers for optimal results.

    Features:
    - Automatic provider selection based on task
    - Fallback chains for reliability
    - Parallel generation for speed
    - Cost optimization
    - Quality scoring and selection
    """

    def __init__(
        self,
        openrouter_key: Optional[str] = None,
        gigachat_key: Optional[str] = None,
        elevenlabs_key: Optional[str] = None,
        heygen_key: Optional[str] = None,
        proxy_url: Optional[str] = None
    ):
        self.proxy_url = proxy_url or os.getenv("OPENROUTER_PROXY_URL")

        # Initialize providers
        self._init_text_providers(openrouter_key, gigachat_key)
        self._init_media_providers(openrouter_key, elevenlabs_key, heygen_key)

    def _init_text_providers(self, openrouter_key: str, gigachat_key: str):
        """Initialize text generation providers."""
        self.text_providers: Dict[str, TextProvider] = {}

        # GigaChat - works in Russia without proxy
        if gigachat_key or os.getenv("GIGACHAT_AUTH_KEY"):
            self.text_providers["gigachat"] = GigaChatProvider(
                auth_key=gigachat_key or os.getenv("GIGACHAT_AUTH_KEY")
            )
            logger.info("GigaChat provider initialized")

        # OpenRouter - access to multiple models
        if openrouter_key or os.getenv("OPENROUTER_API_KEY"):
            api_key = openrouter_key or os.getenv("OPENROUTER_API_KEY")

            self.text_providers["openrouter_gpt4o"] = OpenRouterProvider(
                api_key=api_key,
                model="gpt-4o-mini",
                proxy_url=self.proxy_url
            )

            self.text_providers["openrouter_claude"] = OpenRouterProvider(
                api_key=api_key,
                model="claude-3-haiku",
                proxy_url=self.proxy_url
            )

            self.text_providers["openrouter_mixtral"] = OpenRouterProvider(
                api_key=api_key,
                model="mixtral-8x7b",
                proxy_url=self.proxy_url
            )
            logger.info("OpenRouter providers initialized")

    def _init_media_providers(self, openrouter_key: str, elevenlabs_key: str, heygen_key: str):
        """Initialize media generation providers."""
        # Image provider
        if openrouter_key or os.getenv("OPENROUTER_API_KEY"):
            self.image_provider = OpenRouterImageProvider(
                api_key=openrouter_key or os.getenv("OPENROUTER_API_KEY"),
                proxy_url=self.proxy_url
            )
        else:
            self.image_provider = None

        # Voice provider
        if elevenlabs_key or os.getenv("ELEVENLABS_API_KEY"):
            self.voice_provider = ElevenLabsProvider(
                api_key=elevenlabs_key or os.getenv("ELEVENLABS_API_KEY"),
                proxy_url=self.proxy_url
            )
            logger.info("ElevenLabs provider initialized")
        else:
            self.voice_provider = None

        # Video provider
        if heygen_key or os.getenv("HEYGEN_API_KEY"):
            self.video_provider = HeyGenProvider(
                api_key=heygen_key or os.getenv("HEYGEN_API_KEY"),
                proxy_url=self.proxy_url
            )
            logger.info("HeyGen provider initialized")
        else:
            self.video_provider = None

    def get_best_text_provider(
        self,
        optimize_for: str = "quality"  # quality, speed, cost
    ) -> Tuple[str, TextProvider]:
        """
        Select the best available text provider.

        Args:
            optimize_for: Optimization target (quality, speed, cost)

        Returns:
            Tuple of (provider_name, provider_instance)
        """
        if not self.text_providers:
            raise ValueError("No text providers available")

        available = []
        for name, provider in self.text_providers.items():
            config = PROVIDER_CONFIGS.get(name)
            if config:
                available.append((name, provider, config))

        if not available:
            # Return first available
            name, provider = next(iter(self.text_providers.items()))
            return name, provider

        # Sort by optimization target
        if optimize_for == "quality":
            available.sort(key=lambda x: -x[2].quality_rating)
        elif optimize_for == "speed":
            available.sort(key=lambda x: -x[2].speed_rating)
        elif optimize_for == "cost":
            available.sort(key=lambda x: x[2].cost_per_1k)
        else:
            available.sort(key=lambda x: x[2].priority)

        name, provider, _ = available[0]
        return name, provider

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = None,
        optimize_for: str = "quality",
        json_schema: dict = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using the best available provider.

        Returns:
            Dict with 'content', 'provider', and metadata
        """
        provider_name, provider = self.get_best_text_provider(optimize_for)

        try:
            result = await provider.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                json_schema=json_schema,
                **kwargs
            )

            return {
                "content": result,
                "provider": provider_name,
                "status": "success"
            }

        except Exception as e:
            logger.warning(f"Provider {provider_name} failed: {e}")

            # Try fallback providers
            for name, fallback in self.text_providers.items():
                if name == provider_name:
                    continue
                try:
                    result = await fallback.generate_text(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        json_schema=json_schema,
                        **kwargs
                    )
                    return {
                        "content": result,
                        "provider": name,
                        "status": "success",
                        "fallback": True
                    }
                except Exception as fe:
                    logger.warning(f"Fallback {name} failed: {fe}")
                    continue

            raise Exception(f"All providers failed. Last error: {e}")

    async def generate_parallel(
        self,
        prompt: str,
        system_prompt: str = None,
        providers: List[str] = None,
        select_best: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using multiple providers in parallel.

        Args:
            prompt: User prompt
            system_prompt: System message
            providers: List of provider names to use
            select_best: If True, return only the best result

        Returns:
            Dict with results from all providers or the best one
        """
        if providers is None:
            providers = list(self.text_providers.keys())[:3]  # Top 3

        tasks = []
        for name in providers:
            if name in self.text_providers:
                provider = self.text_providers[name]
                tasks.append(self._generate_with_name(
                    name, provider, prompt, system_prompt, **kwargs
                ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = []
        for result in results:
            if isinstance(result, dict) and result.get("status") == "success":
                successful.append(result)

        if not successful:
            raise Exception("All parallel providers failed")

        if select_best:
            # Select best by provider quality rating
            def quality_score(r):
                config = PROVIDER_CONFIGS.get(r["provider"])
                return config.quality_rating if config else 5

            successful.sort(key=quality_score, reverse=True)
            return successful[0]

        return {"results": successful, "status": "success"}

    async def _generate_with_name(
        self,
        name: str,
        provider: TextProvider,
        prompt: str,
        system_prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Helper for parallel generation."""
        try:
            result = await provider.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )
            return {
                "content": result,
                "provider": name,
                "status": "success"
            }
        except Exception as e:
            return {
                "provider": name,
                "status": "error",
                "error": str(e)
            }

    async def generate_ad_creatives(
        self,
        business_info: str,
        landing_url: str = None,
        generate_images: bool = True,
        generate_voice: bool = False,
        generate_video: bool = False
    ) -> Dict[str, Any]:
        """
        Generate complete ad creatives package.

        Args:
            business_info: Business description
            landing_url: Landing page URL
            generate_images: Generate images
            generate_voice: Generate voiceovers
            generate_video: Generate video ads

        Returns:
            Complete creative package with texts, images, voice, video
        """
        from app.services.magic import TEXT_SYSTEM_PROMPT, TEXT_USER_PROMPT, scrape_landing_page

        # Scrape landing page if provided
        full_info = business_info
        if landing_url:
            scraped = await scrape_landing_page(landing_url)
            full_info = f"{scraped}\n\n{business_info}" if business_info else scraped

        # Generate ad texts
        text_result = await self.generate_text(
            prompt=TEXT_USER_PROMPT.format(business_info=full_info),
            system_prompt=TEXT_SYSTEM_PROMPT,
            json_schema={"type": "object"},
            optimize_for="quality"
        )

        ads_data = text_result["content"]
        if isinstance(ads_data, str):
            import json
            try:
                ads_data = json.loads(ads_data)
            except:
                ads_data = {"ads": [], "business_name": "Business", "business_type": "services"}

        result = {
            "business_name": ads_data.get("business_name", "Business"),
            "business_type": ads_data.get("business_type", "services"),
            "ads": ads_data.get("ads", []),
            "text_provider": text_result.get("provider"),
            "images": [],
            "voiceovers": [],
            "videos": []
        }

        # Generate images in parallel
        if generate_images and self.image_provider:
            image_tasks = []
            themes = ["main product", "happy customer", "team", "process", "result"]

            for theme in themes:
                prompt = f"Professional ad banner for {result['business_type']}: {theme}. Modern, minimal, eye-catching."
                image_tasks.append(self.image_provider.generate_image(prompt))

            images = await asyncio.gather(*image_tasks, return_exceptions=True)
            result["images"] = [
                {"url": img, "theme": themes[i]}
                for i, img in enumerate(images)
                if isinstance(img, str)
            ]

        # Generate voiceovers
        if generate_voice and self.voice_provider:
            ads = result["ads"][:3]  # First 3 ads
            voiceovers = await self.voice_provider.generate_batch_voiceovers(ads)
            result["voiceovers"] = voiceovers

        # Generate videos
        if generate_video and self.video_provider:
            ads = result["ads"][:2]  # First 2 ads for video
            videos = await self.video_provider.create_batch_ad_videos(ads)
            result["videos"] = videos

        return result

    async def generate_full_campaign(
        self,
        business_info: str,
        landing_url: str,
        budget: float,
        platforms: List[str] = None,
        creative_options: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete advertising campaign ready for launch.

        Args:
            business_info: Business description
            landing_url: Landing page URL
            budget: Total campaign budget
            platforms: Target platforms (yandex, vk, ozon)
            creative_options: What to generate (images, voice, video)

        Returns:
            Complete campaign ready for one-click launch
        """
        if platforms is None:
            platforms = ["yandex", "vk"]

        if creative_options is None:
            creative_options = {
                "images": True,
                "voice": False,
                "video": False
            }

        # Generate creatives
        creatives = await self.generate_ad_creatives(
            business_info=business_info,
            landing_url=landing_url,
            generate_images=creative_options.get("images", True),
            generate_voice=creative_options.get("voice", False),
            generate_video=creative_options.get("video", False)
        )

        # Split budget across platforms
        budget_per_platform = budget / len(platforms)

        # Build campaign structure for each platform
        campaigns = []
        for platform in platforms:
            campaign = {
                "platform": platform,
                "name": f"{creatives['business_name']} - {platform.upper()}",
                "budget": budget_per_platform,
                "status": "ready",
                "ads": creatives["ads"],
                "images": creatives["images"],
                "targeting": self._get_default_targeting(platform)
            }
            campaigns.append(campaign)

        return {
            "status": "ready",
            "business_name": creatives["business_name"],
            "business_type": creatives["business_type"],
            "total_budget": budget,
            "platforms": platforms,
            "campaigns": campaigns,
            "creatives": creatives,
            "launch_ready": True
        }

    def _get_default_targeting(self, platform: str) -> Dict[str, Any]:
        """Get default targeting settings for a platform."""
        defaults = {
            "yandex": {
                "regions": ["Russia"],
                "age": "18-65",
                "strategy": "maximum_conversions"
            },
            "vk": {
                "regions": ["Russia"],
                "age": "18-55",
                "interests": ["auto"]
            },
            "ozon": {
                "categories": ["all"],
                "placement": "search"
            }
        }
        return defaults.get(platform, {})


def get_orchestrator() -> MultiAIOrchestrator:
    """Factory function to get the AI orchestrator."""
    return MultiAIOrchestrator()
