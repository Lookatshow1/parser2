"""
Gemini API Provider.

Integration with Google Gemini 3 Pro for text generation.
"""
from typing import Optional, Dict, Any
import httpx
import logging
import os

from app.core.ai.interfaces import TextProvider

logger = logging.getLogger(__name__)


class GeminiProvider(TextProvider):
    """
    Google Gemini API Provider.
    
    Uses Gemini 3 Pro (gemini-3-pro) for high-quality text generation.
    """
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=120.0)
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate text using Gemini API."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        model = "gemini-3-pro"
        url = f"{self.BASE_URL}/models/{model}:generateContent"
        
        # Build content parts
        parts = []
        if system_prompt:
            parts.append({"text": f"System: {system_prompt}\n\n"})
        parts.append({"text": prompt})
        
        # Build request body
        body = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096,
            },
        }
        
        # Add JSON mode if schema provided
        if json_schema:
            body["generationConfig"]["responseMimeType"] = "application/json"
        
        response = await self._client.post(
            url,
            params={"key": self.api_key},
            json=body,
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Extract text from response
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("No response candidates from Gemini")
        
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            raise ValueError("Empty response from Gemini")
        
        return parts[0].get("text", "")
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()


class GeminiFlashProvider(GeminiProvider):
    """
    Gemini 3 Flash - faster, cheaper model.
    """
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate text using Gemini Flash."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        model = "gemini-3-flash"
        url = f"{self.BASE_URL}/models/{model}:generateContent"
        
        parts = []
        if system_prompt:
            parts.append({"text": f"System: {system_prompt}\n\n"})
        parts.append({"text": prompt})
        
        body = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            },
        }
        
        if json_schema:
            body["generationConfig"]["responseMimeType"] = "application/json"
        
        response = await self._client.post(
            url,
            params={"key": self.api_key},
            json=body,
        )
        response.raise_for_status()
        
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("No response candidates from Gemini")
        
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            raise ValueError("Empty response from Gemini")
        
        return parts[0].get("text", "")


def get_gemini_provider(model: str = "gemini-3-pro") -> GeminiProvider:
    """Get Gemini provider for specified model."""
    if model == "gemini-3-flash":
        return GeminiFlashProvider()
    return GeminiProvider()
