import random
import asyncio
from typing import Any
from .interfaces import TextProvider, ImageProvider, WebScanner

class MockTextProvider(TextProvider):
    async def generate_text(self, prompt: str, system: str | None = None, temperature: float = 0.7, json_schema: dict | None = None) -> str | dict:
        await asyncio.sleep(0.5)
        if json_schema:
            return {
                "campaign_name": "Mock Campaign",
                "ad_groups": [
                    {
                        "name": "Group A",
                        "keywords": ["buy", "now"],
                        "ads": [{"title": "Best Product", "text": "Buy it now"}]
                    }
                ]
            }
        return "This is a mock AI response."

class MockImageProvider(ImageProvider):
    async def generate_images(self, prompt: str, n: int = 1, size: str = "1024x1024") -> list[str]:
        await asyncio.sleep(0.5)
        return ["https://via.placeholder.com/1024"] * n

class MockWebScanner(WebScanner):
    async def fetch_site_profile(self, domain: str) -> dict:
        await asyncio.sleep(0.5)
        return {
            "title": f"Mock Title for {domain}",
            "description": "Mock description of the website.",
            "summary": "This website sells things."
        }
