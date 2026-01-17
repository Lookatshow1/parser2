"""
DALL-E Image Generation Provider.

Integration with OpenAI DALL-E 3 for ad creative image generation.
"""
from typing import Optional, List
import httpx
import logging
import os

from app.core.ai.interfaces import ImageProvider

logger = logging.getLogger(__name__)


class DalleProvider(ImageProvider):
    """
    OpenAI DALL-E 3 Image Generation Provider.
    
    Generates high-quality ad banners and creatives.
    """
    
    BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=120.0)
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "hd",
        style: str = "vivid",
        n: int = 1,
    ) -> List[str]:
        """
        Generate images using DALL-E 3.
        
        Args:
            prompt: Image description
            size: "1024x1024", "1792x1024", "1024x1792"
            quality: "standard" or "hd"
            style: "vivid" or "natural"
            n: Number of images (DALL-E 3 only supports n=1)
        
        Returns:
            List of image URLs
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        # Enhance prompt for ad creatives
        enhanced_prompt = self._enhance_ad_prompt(prompt)
        
        response = await self._client.post(
            f"{self.BASE_URL}/images/generations",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "dall-e-3",
                "prompt": enhanced_prompt,
                "size": size,
                "quality": quality,
                "style": style,
                "n": 1,  # DALL-E 3 only supports 1
            },
        )
        response.raise_for_status()
        
        data = response.json()
        images = data.get("data", [])
        
        return [img["url"] for img in images]
    
    def _enhance_ad_prompt(self, prompt: str) -> str:
        """Enhance prompt for better ad creative output."""
        base_instructions = """
Create a professional advertising banner image. Requirements:
- Clean, modern design
- High contrast for readability
- No text or words on the image
- Professional photography or high-quality 3D render
- Suitable for digital advertising (web, social media)
- Eye-catching and engaging
"""
        return f"{base_instructions}\n\nSubject: {prompt}"
    
    async def generate_ad_banner(
        self,
        business_type: str,
        theme: str,
        format: str = "square",
    ) -> str:
        """
        Generate an ad banner for a specific business.
        
        Args:
            business_type: Type of business (restaurant, ecommerce, etc.)
            theme: Creative theme (sale, new product, etc.)
            format: "square" (1024x1024), "landscape" (1792x1024), "portrait" (1024x1792)
        
        Returns:
            Image URL
        """
        size_map = {
            "square": "1024x1024",
            "landscape": "1792x1024",
            "portrait": "1024x1792",
        }
        
        prompt = f"""
Professional advertising banner for {business_type}.
Theme: {theme}
Style: Modern, clean, premium look
Purpose: Digital advertising campaign
"""
        
        urls = await self.generate_image(
            prompt=prompt,
            size=size_map.get(format, "1024x1024"),
            quality="hd",
        )
        
        return urls[0] if urls else ""
    
    async def generate_product_showcase(
        self,
        product_name: str,
        style: str = "minimalist",
    ) -> str:
        """Generate a product showcase image."""
        prompt = f"""
Product showcase photography for: {product_name}
Style: {style}, professional product photography
Background: Clean, soft gradient
Lighting: Studio lighting, soft shadows
Purpose: E-commerce and advertising
"""
        
        urls = await self.generate_image(prompt=prompt, quality="hd")
        return urls[0] if urls else ""
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()


def get_dalle_provider() -> DalleProvider:
    """Get DALL-E provider instance."""
    return DalleProvider()
