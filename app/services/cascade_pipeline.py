"""
Cascade Image Generation Pipeline.

Connects website scanning → AI text analysis → image prompt generation → DALL-E.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import json
import re

from app.services.platform_strategies import get_strategy
from app.core.ai.openai_provider import get_text_provider
from app.core.ai.dalle_provider import DalleProvider

logger = logging.getLogger(__name__)


@dataclass
class GeneratedCreative:
    """Complete generated creative with text and image."""
    title: str
    text: str
    approach: str
    image_prompt: str
    image_url: Optional[str] = None
    platform: str = "yandex"


@dataclass
class CascadeResult:
    """Result of cascade generation."""
    business_name: str
    business_type: str
    landing_url: str
    platform: str
    creatives: List[GeneratedCreative]
    scan_data: Dict[str, Any]
    generated_at: datetime


class CascadeImagePipeline:
    """
    Full cascade pipeline:
    1. Scan website/URL using platform strategy
    2. Generate text ads with AI
    3. Create image prompts from ad context
    4. Generate images with DALL-E
    """
    
    def __init__(self):
        self.text_provider = get_text_provider()
        self.image_provider = DalleProvider()
    
    async def generate(
        self,
        landing_url: str,
        platform: str = "yandex",
        description: Optional[str] = None,
        generate_images: bool = True,
        image_count: int = 3,
    ) -> CascadeResult:
        """
        Run full cascade generation.
        
        Args:
            landing_url: URL to scan
            platform: Target platform (yandex, vk, ozon)
            description: Optional business description
            generate_images: Whether to generate images
            image_count: Number of images to generate
        """
        logger.info(f"Starting cascade generation for {landing_url} ({platform})")
        
        # Step 1: Scan with platform-specific strategy
        strategy = get_strategy(platform)
        scan_data = await strategy.scan_and_analyze(landing_url)
        
        logger.info(f"Scan complete: {len(scan_data.get('keywords', []))} keywords found")
        
        # Step 2: Generate text ads
        prompt = strategy.build_generation_prompt(scan_data, description or "")
        
        try:
            response = await self.text_provider.generate_text(
                prompt=prompt,
                temperature=0.8,
            )
            
            # Parse JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                raise ValueError("No JSON in AI response")
            
            ads_data = json.loads(json_match.group())
        except Exception as e:
            logger.exception(f"Error generating text: {e}")
            ads_data = {"business_name": "Unknown", "ads": []}
        
        # Extract business info
        business_name = ads_data.get("business_name", "Business")
        business_type = ads_data.get("business_type", scan_data.get("main_page", {}).get("title", ""))
        
        # Step 3: Create creatives with image prompts
        creatives = []
        ads = ads_data.get("ads", []) or ads_data.get("search_ads", []) or ads_data.get("posts", [])
        
        for i, ad in enumerate(ads[:10]):  # Limit to 10 ads
            title = ad.get("title", ad.get("title1", ""))
            text = ad.get("text", ad.get("description", ""))
            approach = ad.get("approach", "benefit")
            
            # Generate image prompt from ad context
            image_prompt = self._create_image_prompt(
                business_type=business_type,
                title=title,
                approach=approach,
            )
            
            creatives.append(GeneratedCreative(
                title=title,
                text=text,
                approach=approach,
                image_prompt=image_prompt,
                platform=platform,
            ))
        
        # Step 4: Generate images (for top N creatives)
        if generate_images and creatives:
            await self._generate_images(creatives[:image_count])
        
        return CascadeResult(
            business_name=business_name,
            business_type=business_type,
            landing_url=landing_url,
            platform=platform,
            creatives=creatives,
            scan_data=scan_data,
            generated_at=datetime.utcnow(),
        )
    
    def _create_image_prompt(
        self,
        business_type: str,
        title: str,
        approach: str,
    ) -> str:
        """Create DALL-E prompt from ad context."""
        
        # Map approaches to visual styles
        style_map = {
            "urgency": "dynamic, energetic, bold colors, sense of movement",
            "scarcity": "exclusive, premium, limited edition feel, elegant",
            "social_proof": "people, community, trust, warm and inviting",
            "authority": "professional, corporate, trustworthy, clean",
            "benefit": "bright, positive, aspirational, lifestyle",
            "problem_solution": "before/after feel, transformation, contrast",
            "emotional": "emotional, warm, human connection, heartfelt",
            "rational": "clean, data-driven, infographic style, modern",
            "curiosity": "mysterious, intriguing, artistic, creative",
        }
        
        style = style_map.get(approach, "modern, professional, eye-catching")
        
        prompt = f"""Professional advertising banner for {business_type}.

Visual theme: {title}
Style: {style}
Requirements:
- High quality, commercial photography or 3D render
- No text or words on the image
- Clean composition, suitable for digital advertising
- Vibrant colors that attract attention
- Professional and premium look
- Square format (1024x1024)"""
        
        return prompt
    
    async def _generate_images(self, creatives: List[GeneratedCreative]):
        """Generate images for creatives using DALL-E."""
        for creative in creatives:
            try:
                urls = await self.image_provider.generate_image(
                    prompt=creative.image_prompt,
                    size="1024x1024",
                    quality="hd",
                )
                if urls:
                    creative.image_url = urls[0]
                    logger.info(f"Generated image for: {creative.title[:30]}...")
            except Exception as e:
                logger.warning(f"Failed to generate image: {e}")
    
    async def regenerate_image(
        self,
        creative: GeneratedCreative,
        style_override: Optional[str] = None,
    ) -> Optional[str]:
        """Regenerate image for a specific creative."""
        prompt = creative.image_prompt
        if style_override:
            prompt = f"{prompt}\n\nAdditional style: {style_override}"
        
        try:
            urls = await self.image_provider.generate_image(
                prompt=prompt,
                size="1024x1024",
                quality="hd",
            )
            if urls:
                creative.image_url = urls[0]
                return urls[0]
        except Exception as e:
            logger.exception(f"Error regenerating image: {e}")
        
        return None
    
    async def close(self):
        """Close providers."""
        await self.image_provider.close()


# Convenience function
async def cascade_generate(
    landing_url: str,
    platform: str = "yandex",
    description: Optional[str] = None,
    generate_images: bool = True,
) -> CascadeResult:
    """Run cascade generation pipeline."""
    pipeline = CascadeImagePipeline()
    try:
        return await pipeline.generate(
            landing_url=landing_url,
            platform=platform,
            description=description,
            generate_images=generate_images,
        )
    finally:
        await pipeline.close()
