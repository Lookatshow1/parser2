"""
GigaChat AI Provider

Implements Sber GigaChat API for text generation.
https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/post-chat
"""
import os
import json
import logging
import uuid
import time
from typing import Optional
import httpx

from app.core.ai.interfaces import TextProvider

logger = logging.getLogger(__name__)


class GigaChatProvider(TextProvider):
    """
    Sber GigaChat text generation provider.
    
    Requires:
        - GIGACHAT_AUTH_KEY: Base64-encoded credentials (ClientId:ClientSecret)
        - GIGACHAT_SCOPE: API scope (GIGACHAT_API_PERS for personal use)
    """
    
    OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    
    def __init__(
        self, 
        auth_key: Optional[str] = None, 
        scope: str = None,
        model: str = "GigaChat"
    ):
        self.auth_key = auth_key or os.getenv("GIGACHAT_AUTH_KEY")
        self.scope = scope or os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.model = model
        
        # Token caching
        self._access_token: Optional[str] = None
        self._token_expires_at: int = 0
        
        if not self.auth_key:
            logger.warning("GIGACHAT_AUTH_KEY not set - GigaChat provider will not work")
    
    async def _get_access_token(self) -> str:
        """
        Gets or refreshes the access token.
        Token is cached and reused until 5 minutes before expiration.
        """
        current_time = int(time.time() * 1000)
        
        # Return cached token if still valid (with 5 min buffer)
        if self._access_token and current_time < (self._token_expires_at - 300000):
            return self._access_token
        
        logger.info("Obtaining new GigaChat access token...")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {self.auth_key}"
        }
        
        data = {"scope": self.scope}
        
        try:
            async with httpx.AsyncClient(
                timeout=30.0, 
                verify=False  # GigaChat uses self-signed certs
            ) as client:
                response = await client.post(
                    self.OAUTH_URL,
                    headers=headers,
                    data=data
                )
                
                response.raise_for_status()
                result = response.json()
                
                self._access_token = result["access_token"]
                self._token_expires_at = result["expires_at"]
                
                logger.info("GigaChat access token obtained successfully")
                return self._access_token
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GigaChat OAuth error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to obtain GigaChat token: {e.response.status_code}")
        except Exception as e:
            logger.exception("GigaChat OAuth request failed")
            raise
    
    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: str = None,
        temperature: float = 0.7,
        json_schema: dict = None
    ) -> dict | str:
        """
        Generates text using GigaChat API.
        """
        if not self.auth_key:
            raise ValueError("GIGACHAT_AUTH_KEY not configured")
        
        access_token = await self._get_access_token()
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        request_body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2000,
            "stream": False,
            "repetition_penalty": 1.0
        }
        
        try:
            async with httpx.AsyncClient(
                timeout=120.0,
                verify=False  # GigaChat uses self-signed certs
            ) as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json=request_body
                )
                
                if response.status_code == 401:
                    # Token expired, refresh and retry once
                    self._access_token = None
                    access_token = await self._get_access_token()
                    response = await client.post(
                        self.API_URL,
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        },
                        json=request_body
                    )
                
                if response.status_code == 429:
                    raise Exception("GigaChat rate limit exceeded. Please try again later.")
                
                response.raise_for_status()
                data = response.json()
                
                content = data["choices"][0]["message"]["content"]
                
                # Log usage for monitoring
                usage = data.get("usage", {})
                logger.info(
                    f"GigaChat usage: prompt={usage.get('prompt_tokens', 0)}, "
                    f"completion={usage.get('completion_tokens', 0)}, "
                    f"total={usage.get('total_tokens', 0)}"
                )
                
                # Try to parse as JSON if schema was requested
                if json_schema:
                    try:
                        # GigaChat may return JSON in markdown code blocks
                        cleaned_content = content.strip()
                        if cleaned_content.startswith("```"):
                            # Remove markdown code block markers
                            lines = cleaned_content.split("\n")
                            cleaned_content = "\n".join(lines[1:-1])
                        return json.loads(cleaned_content)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse GigaChat response as JSON")
                        # Try to extract JSON from the response
                        import re
                        json_match = re.search(r'\{[\s\S]*\}', content)
                        if json_match:
                            try:
                                return json.loads(json_match.group())
                            except json.JSONDecodeError:
                                pass
                        return {"raw_text": content}
                
                return content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GigaChat API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"GigaChat API error: {e.response.status_code}")
        except Exception as e:
            logger.exception("GigaChat request failed")
            raise


def get_gigachat_provider() -> GigaChatProvider:
    """Factory function to get GigaChat provider."""
    return GigaChatProvider()
