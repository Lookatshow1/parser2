"""
HeyGen AI Video Provider

AI-powered video generation for advertisements.
https://docs.heygen.com/reference/
"""
import os
import logging
import asyncio
from typing import Optional, List, Dict, Any
import httpx

logger = logging.getLogger(__name__)


# Popular HeyGen avatars for Russian market
HEYGEN_AVATARS = {
    # Professional presenters
    "anna_professional": "Anna_public_3_20240108",
    "alex_business": "Alex_public_pro_20240108",
    "maria_friendly": "Maria_public_2_20240108",

    # Casual/young
    "josh_casual": "Josh_lite_front_20240108",
    "emma_energetic": "Emma_public_lite_20240108",

    # Realistic avatars
    "presenter_male": "wayne_20240108",
    "presenter_female": "monica_20240108",

    # Custom/animated
    "animated_presenter": "animated_kyra_20240108",
}


# Video templates optimized for ads
HEYGEN_TEMPLATES = {
    "product_showcase": {
        "background": "office_modern",
        "avatar_position": "right",
        "text_position": "left"
    },
    "announcement": {
        "background": "gradient_blue",
        "avatar_position": "center",
        "text_position": "bottom"
    },
    "testimonial": {
        "background": "living_room",
        "avatar_position": "left",
        "text_position": "right"
    },
    "promo": {
        "background": "studio_colorful",
        "avatar_position": "center",
        "text_position": "overlay"
    }
}


class HeyGenProvider:
    """
    HeyGen AI video generation provider.

    Features:
    - AI avatar videos
    - Text-to-video conversion
    - Multiple templates for ads
    - Russian language support
    """

    API_URL = "https://api.heygen.com/v2"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_avatar: str = "anna_professional",
        proxy_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("HEYGEN_API_KEY")
        self.default_avatar = HEYGEN_AVATARS.get(default_avatar, default_avatar)
        self.proxy_url = proxy_url or os.getenv("HEYGEN_PROXY_URL")

        if not self.api_key:
            logger.warning("HEYGEN_API_KEY not set - HeyGen provider will not work")

    def _get_http_client(self) -> httpx.AsyncClient:
        """Creates HTTP client with optional proxy."""
        kwargs = {
            "timeout": 120.0,
            "headers": {
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
        }

        if self.proxy_url:
            kwargs["proxy"] = self.proxy_url

        return httpx.AsyncClient(**kwargs)

    async def create_video(
        self,
        script: str,
        avatar: str = None,
        voice: str = None,
        background: str = "office_modern",
        dimension: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """
        Create an AI video with avatar speaking the script.

        Args:
            script: Text for the avatar to speak
            avatar: Avatar ID or preset name
            voice: Voice ID (auto-selected if not provided)
            background: Background preset or URL
            dimension: Video dimensions (default 1920x1080)

        Returns:
            Dict with video_id and status
        """
        if not self.api_key:
            raise ValueError("HEYGEN_API_KEY not configured")

        avatar_id = HEYGEN_AVATARS.get(avatar, avatar) if avatar else self.default_avatar

        if dimension is None:
            dimension = {"width": 1920, "height": 1080}

        request_body = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script,
                        "voice_id": voice or "ru-RU-DmitryNeural"  # Russian voice
                    },
                    "background": {
                        "type": "color",
                        "value": "#f0f0f0"
                    }
                }
            ],
            "dimension": dimension,
            "aspect_ratio": "16:9"
        }

        try:
            async with self._get_http_client() as client:
                response = await client.post(
                    f"{self.API_URL}/video/generate",
                    json=request_body
                )

                if response.status_code == 401:
                    raise ValueError("Invalid HeyGen API key")
                if response.status_code == 429:
                    raise Exception("HeyGen rate limit exceeded")

                response.raise_for_status()
                data = response.json()

                video_id = data.get("data", {}).get("video_id")
                logger.info(f"HeyGen video created: {video_id}")

                return {
                    "video_id": video_id,
                    "status": "processing",
                    "script_length": len(script)
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"HeyGen API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.exception("HeyGen request failed")
            raise

    async def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Check the status of a video generation.

        Returns:
            Dict with status, video_url (if complete), and other metadata
        """
        if not self.api_key:
            raise ValueError("HEYGEN_API_KEY not configured")

        try:
            async with self._get_http_client() as client:
                response = await client.get(
                    f"{self.API_URL}/video_status.get",
                    params={"video_id": video_id}
                )

                response.raise_for_status()
                data = response.json()

                result = data.get("data", {})
                return {
                    "video_id": video_id,
                    "status": result.get("status"),
                    "video_url": result.get("video_url"),
                    "thumbnail_url": result.get("thumbnail_url"),
                    "duration": result.get("duration"),
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Failed to get video status: {e}")
            return {"video_id": video_id, "status": "error", "error": str(e)}

    async def wait_for_video(
        self,
        video_id: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 10
    ) -> Dict[str, Any]:
        """
        Wait for video generation to complete.

        Args:
            video_id: The video ID to monitor
            max_wait_seconds: Maximum time to wait
            poll_interval: Seconds between status checks

        Returns:
            Final status dict with video_url if successful
        """
        elapsed = 0

        while elapsed < max_wait_seconds:
            status = await self.get_video_status(video_id)

            if status.get("status") == "completed":
                logger.info(f"Video {video_id} completed: {status.get('video_url')}")
                return status

            if status.get("status") == "failed":
                logger.error(f"Video {video_id} failed: {status.get('error')}")
                return status

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        return {"video_id": video_id, "status": "timeout", "error": "Video generation timed out"}

    async def create_ad_video(
        self,
        ad_title: str,
        ad_text: str,
        template: str = "product_showcase",
        avatar: str = None
    ) -> Dict[str, Any]:
        """
        Create a video advertisement.

        Args:
            ad_title: Ad headline
            ad_text: Ad body text
            template: Video template preset
            avatar: Avatar to use

        Returns:
            Dict with video creation result
        """
        # Combine title and text into a natural script
        script = f"{ad_title}. {ad_text}"

        # Get template settings
        template_config = HEYGEN_TEMPLATES.get(template, HEYGEN_TEMPLATES["product_showcase"])

        try:
            result = await self.create_video(
                script=script,
                avatar=avatar,
                background=template_config.get("background", "office_modern")
            )

            result["ad_title"] = ad_title
            result["template"] = template
            return result

        except Exception as e:
            logger.error(f"Failed to create ad video: {e}")
            return {
                "error": str(e),
                "ad_title": ad_title,
                "status": "failed"
            }

    async def create_batch_ad_videos(
        self,
        ads: List[Dict[str, str]],
        template: str = "promo"
    ) -> List[Dict[str, Any]]:
        """
        Create videos for multiple ads.

        Args:
            ads: List of dicts with 'title' and 'text' keys
            template: Video template to use

        Returns:
            List of video creation results
        """
        results = []

        for ad in ads:
            result = await self.create_ad_video(
                ad_title=ad.get("title", ""),
                ad_text=ad.get("text", ""),
                template=template
            )
            results.append(result)

            # Rate limiting - wait between requests
            await asyncio.sleep(2)

        return results

    async def list_avatars(self) -> List[Dict[str, Any]]:
        """Get available avatars from HeyGen."""
        if not self.api_key:
            return list(HEYGEN_AVATARS.items())

        try:
            async with self._get_http_client() as client:
                response = await client.get(f"{self.API_URL}/avatars")
                response.raise_for_status()
                data = response.json()

                return [
                    {
                        "avatar_id": a["avatar_id"],
                        "name": a.get("avatar_name", "Unknown"),
                        "gender": a.get("gender", "unknown"),
                        "preview_url": a.get("preview_image_url")
                    }
                    for a in data.get("data", {}).get("avatars", [])
                ]

        except Exception as e:
            logger.error(f"Failed to list avatars: {e}")
            return []


def get_heygen_provider() -> HeyGenProvider:
    """Factory function to get HeyGen provider."""
    return HeyGenProvider()
