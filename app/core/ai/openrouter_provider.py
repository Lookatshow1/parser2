"""
OpenRouter AI Provider

Universal access to multiple AI models through OpenRouter.
Supports proxy for Russia-based servers.
https://openrouter.ai/docs
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
import httpx

from app.core.ai.interfaces import TextProvider, ImageProvider

logger = logging.getLogger(__name__)


# Available models on OpenRouter (sorted by capability)
OPENROUTER_MODELS = {
    # Top tier - best quality
    "claude-3-opus": "anthropic/claude-3-opus",
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    "gpt-4-turbo": "openai/gpt-4-turbo",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",

    # Mid tier - good balance
    "claude-3-sonnet": "anthropic/claude-3-sonnet",
    "claude-3-haiku": "anthropic/claude-3-haiku",
    "gemini-pro": "google/gemini-pro",
    "gemini-1.5-pro": "google/gemini-1.5-pro",
    "gemini-1.5-flash": "google/gemini-1.5-flash",

    # Open source - fast and cheap
    "llama-3.1-70b": "meta-llama/llama-3.1-70b-instruct",
    "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
    "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct",
    "mistral-7b": "mistralai/mistral-7b-instruct",
    "qwen-72b": "qwen/qwen-2-72b-instruct",

    # Russian-friendly
    "yandexgpt": "yandex/yandexgpt",

    # Coding specialists
    "deepseek-coder": "deepseek/deepseek-coder",
    "codellama-34b": "codellama/codellama-34b-instruct",

    # Creative
    "claude-instant": "anthropic/claude-instant-1.2",

    # Image models
    "dall-e-3": "openai/dall-e-3",
    "stable-diffusion-xl": "stability/stable-diffusion-xl",
    "midjourney": "midjourney/midjourney",
}


class OpenRouterProvider(TextProvider):
    """
    OpenRouter-based text generation provider.
    Access to 100+ AI models through a single API.

    Features:
    - Automatic model fallback
    - Proxy support for Russia
    - Cost optimization
    - Rate limit handling
    """

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        proxy_url: Optional[str] = None,
        site_url: str = "https://effecto.ru",
        site_name: str = "Effecto AI Ads"
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = OPENROUTER_MODELS.get(model, model)
        self.proxy_url = proxy_url or os.getenv("OPENROUTER_PROXY_URL")
        self.site_url = site_url
        self.site_name = site_name

        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set - OpenRouter provider will not work")

    def _get_http_client(self) -> httpx.AsyncClient:
        """Creates HTTP client with optional proxy support."""
        kwargs = {
            "timeout": 120.0,
            "headers": {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.site_url,
                "X-Title": self.site_name
            }
        }

        if self.proxy_url:
            kwargs["proxy"] = self.proxy_url
            logger.info(f"Using proxy: {self.proxy_url[:20]}...")

        return httpx.AsyncClient(**kwargs)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        json_schema: dict = None,
        model: str = None
    ) -> dict | str:
        """
        Generates text using OpenRouter API.

        Args:
            prompt: User prompt
            system_prompt: Optional system message
            temperature: Creativity (0-1)
            json_schema: Optional JSON schema for structured output
            model: Override default model
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        use_model = OPENROUTER_MODELS.get(model, model) if model else self.model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        request_body = {
            "model": use_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4000,
        }

        # JSON mode for supported models
        if json_schema and ("gpt" in use_model or "claude" in use_model):
            request_body["response_format"] = {"type": "json_object"}

        try:
            async with self._get_http_client() as client:
                response = await client.post(self.API_URL, json=request_body)

                if response.status_code == 429:
                    # Rate limited - try cheaper model
                    logger.warning(f"Rate limited on {use_model}, falling back to mixtral")
                    request_body["model"] = OPENROUTER_MODELS["mixtral-8x7b"]
                    response = await client.post(self.API_URL, json=request_body)

                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]

                # Log usage and cost
                usage = data.get("usage", {})
                logger.info(
                    f"OpenRouter [{use_model}]: "
                    f"tokens={usage.get('total_tokens', 0)}"
                )

                # Parse JSON if requested
                if json_schema:
                    return self._parse_json_response(content)

                return content

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"OpenRouter API error: {e.response.status_code}")
        except Exception as e:
            logger.exception("OpenRouter request failed")
            raise

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from response, handling markdown code blocks."""
        try:
            # Direct parse
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try removing markdown code blocks
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Extract JSON object
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"raw_text": content}

    async def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: str = None,
        models: List[str] = None,
        **kwargs
    ) -> dict | str:
        """
        Try multiple models in sequence until one succeeds.

        Args:
            prompt: User prompt
            system_prompt: System message
            models: List of models to try (defaults to smart selection)
        """
        if models is None:
            models = ["gpt-4o-mini", "claude-3-haiku", "mixtral-8x7b", "llama-3.1-8b"]

        last_error = None
        for model in models:
            try:
                return await self.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=model,
                    **kwargs
                )
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                last_error = e
                continue

        raise Exception(f"All models failed. Last error: {last_error}")


class OpenRouterImageProvider(ImageProvider):
    """
    Image generation through OpenRouter.
    Supports DALL-E 3, Stable Diffusion XL, etc.
    """

    API_URL = "https://openrouter.ai/api/v1/images/generations"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "dall-e-3",
        proxy_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = OPENROUTER_MODELS.get(model, model)
        self.proxy_url = proxy_url or os.getenv("OPENROUTER_PROXY_URL")

    async def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        """Generate a single image from prompt."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        request_body = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "n": 1
        }

        kwargs = {
            "timeout": 120.0,
            "headers": {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        }

        if self.proxy_url:
            kwargs["proxy"] = self.proxy_url

        try:
            async with httpx.AsyncClient(**kwargs) as client:
                response = await client.post(self.API_URL, json=request_body)
                response.raise_for_status()
                data = response.json()

                return data["data"][0]["url"]

        except Exception as e:
            logger.warning(f"OpenRouter image generation failed: {e}")
            # Return placeholder
            import hashlib
            seed = hashlib.md5(prompt.encode()).hexdigest()[:8]
            return f"https://picsum.photos/seed/{seed}/1024/1024"


def get_openrouter_provider(model: str = "gpt-4o-mini") -> OpenRouterProvider:
    """Factory function to get OpenRouter provider."""
    return OpenRouterProvider(model=model)


def get_openrouter_image_provider(model: str = "dall-e-3") -> OpenRouterImageProvider:
    """Factory function to get OpenRouter image provider."""
    return OpenRouterImageProvider(model=model)
