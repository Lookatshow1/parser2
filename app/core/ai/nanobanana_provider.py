"""
Nano Banana Image Provider - High-quality marketing banner generation.

Uses Gemini 2.5/3 Flash Image (Nano Banana) for generating banners
with proper text rendering for advertising creatives.
"""
import logging
import httpx
from typing import Optional
import os
import json

from app.core.ai.interfaces import ImageProvider

logger = logging.getLogger(__name__)


class NanoBananaProvider(ImageProvider):
    """
    Generate marketing banners with Nano Banana (Gemini Image) API.
    
    Key features:
    - High-fidelity text rendering on images
    - Consistent visual style
    - Marketing-optimized compositions
    """
    
    API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("No Google AI API key found, NanoBananaProvider will use fallback")
    
    async def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        """Generate image from text prompt."""
        return await self.generate_banner(
            headline="",
            subline="",
            style_prompt=prompt
        )
    
    async def generate_banner(
        self,
        headline: str,
        subline: str,
        business_type: str = "business",
        style: str = "modern",
        style_prompt: str = "",
        size: str = "1080x1080"
    ) -> str:
        """
        Generate marketing banner with text overlay.
        
        Args:
            headline: Main banner headline (short, impactful)
            subline: Supporting text or CTA
            business_type: Type of business for visual context
            style: Visual style (modern, minimal, bold, premium)
            style_prompt: Additional custom prompt
            size: Output size (1080x1080, 1200x628, 1080x1920)
            
        Returns:
            URL to generated image
        """
        if not self.api_key:
            # Fallback to placeholder
            return f"https://picsum.photos/seed/{hash(headline) % 1000}/400/400"
        
        # Build optimized prompt for Nano Banana
        prompt = self._build_banner_prompt(
            headline=headline,
            subline=subline,
            business_type=business_type,
            style=style,
            custom_prompt=style_prompt,
            size=size
        )
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.API_BASE}?key={self.api_key}",
                    json={
                        "contents": [{
                            "parts": [{
                                "text": prompt
                            }]
                        }],
                        "generationConfig": {
                            "responseModalities": ["Text", "Image"],
                            "temperature": 0.7
                        }
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Nano Banana API error: {response.text}")
                    return f"https://picsum.photos/seed/{hash(prompt) % 1000}/400/400"
                
                data = response.json()
                
                # Extract image from response
                for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        # For inline base64 images, we'd need to upload to storage
                        # For now, use the data URL directly
                        mime = part["inlineData"]["mimeType"]
                        b64 = part["inlineData"]["data"]
                        return f"data:{mime};base64,{b64}"
                
                # Fallback
                return f"https://picsum.photos/seed/{hash(prompt) % 1000}/400/400"
                
        except Exception as e:
            logger.exception(f"Nano Banana generation failed: {e}")
            return f"https://picsum.photos/seed/{hash(prompt) % 1000}/400/400"
    
    def _build_banner_prompt(
        self,
        headline: str,
        subline: str,
        business_type: str,
        style: str,
        custom_prompt: str,
        size: str
    ) -> str:
        """Build optimized prompt for banner generation."""
        
        style_descriptions = {
            "modern": "clean, minimalist, with subtle gradients and modern typography",
            "bold": "vibrant colors, bold typography, high contrast, eye-catching",
            "premium": "luxury aesthetic, dark backgrounds, gold accents, elegant",
            "minimal": "white space, simple shapes, understated elegance",
            "tech": "futuristic, dark mode, neon accents, geometric patterns"
        }
        
        style_desc = style_descriptions.get(style, style_descriptions["modern"])
        
        aspect_hints = {
            "1080x1080": "square format for social media feed",
            "1200x628": "horizontal format for Facebook/LinkedIn ads", 
            "1080x1920": "vertical stories format for Instagram/TikTok",
            "300x250": "medium rectangle web banner",
            "728x90": "leaderboard web banner"
        }
        
        aspect = aspect_hints.get(size, "square format")
        
        prompt_parts = [
            f"Create a professional marketing banner image for {business_type}.",
            f"Style: {style_desc}.",
            f"Format: {aspect}.",
        ]
        
        if headline:
            prompt_parts.append(f'Include the headline text: "{headline}" prominently displayed.')
        
        if subline:
            prompt_parts.append(f'Include subtext: "{subline}" in smaller text.')
        
        prompt_parts.extend([
            "The image should look professional and suitable for online advertising.",
            "Text should be clearly readable with good contrast.",
            "Use appropriate visual elements that relate to the business type.",
            "No placeholder text or lorem ipsum - only the specified text."
        ])
        
        if custom_prompt:
            prompt_parts.append(custom_prompt)
        
        return " ".join(prompt_parts)


def get_nanobanana_provider() -> NanoBananaProvider:
    """Factory function to get Nano Banana provider."""
    return NanoBananaProvider()
