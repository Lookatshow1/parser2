import os
import json
import logging
from typing import Optional
from app.core.ai.interfaces import TextProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(TextProvider):
    """
    OpenAI GPT-based text generation provider.
    Requires OPENAI_API_KEY environment variable.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - OpenAI provider will not work")
    
    async def generate_text(self, prompt: str, json_schema: dict = None) -> dict | str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        import httpx
        
        messages = [
            {"role": "system", "content": "You are an expert advertising copywriter. Generate creative, engaging ad campaigns in JSON format."},
            {"role": "user", "content": prompt}
        ]
        
        request_body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        
        # If JSON schema provided, use response_format
        if json_schema:
            request_body["response_format"] = {"type": "json_object"}
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )
                
                if response.status_code == 429:
                    raise Exception("Rate limit exceeded. Please try again later.")
                
                response.raise_for_status()
                data = response.json()
                
                content = data["choices"][0]["message"]["content"]
                
                # Try to parse as JSON if schema was requested
                if json_schema:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse response as JSON, returning raw text")
                        return {"raw_text": content}
                
                return content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"OpenAI API error: {e.response.status_code}")
        except Exception as e:
            logger.exception("OpenAI request failed")
            raise


def get_text_provider() -> TextProvider:
    """
    Factory function to get the appropriate text provider.
    Uses OpenAI if API key is configured, otherwise falls back to mock.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        logger.info("Using OpenAI provider")
        return OpenAIProvider(api_key=api_key)
    else:
        logger.info("OPENAI_API_KEY not set, using mock provider")
        from app.core.ai.mock_provider import MockTextProvider
        return MockTextProvider()
