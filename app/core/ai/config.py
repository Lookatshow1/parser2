"""
AI Provider Configuration

This module provides configuration for AI providers.
Priority: GIGACHAT > OPENAI > ANTHROPIC > MOCK
"""
import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class AIProviderType(str, Enum):
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GIGACHAT = "gigachat"


class AIConfig(BaseModel):
    provider: AIProviderType = AIProviderType.MOCK
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gigachat_auth_key: Optional[str] = None
    gigachat_scope: Optional[str] = None
    model: str = "GigaChat"
    temperature: float = 0.7
    max_tokens: int = 2000


def get_ai_config() -> AIConfig:
    """
    Get AI configuration from environment variables.
    Automatically detects available providers.
    Priority: GIGACHAT > OPENAI > ANTHROPIC > MOCK
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    gigachat_key = os.getenv("GIGACHAT_AUTH_KEY")
    gigachat_scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    
    # Auto-detect provider based on available keys
    # Priority: GigaChat (works in Russia) > OpenAI > Anthropic > Mock
    provider = AIProviderType.MOCK
    model = "mock"
    
    if gigachat_key:
        provider = AIProviderType.GIGACHAT
        model = os.getenv("AI_MODEL", "GigaChat")
    elif openai_key:
        provider = AIProviderType.OPENAI
        model = os.getenv("AI_MODEL", "gpt-4o-mini")
    elif anthropic_key:
        provider = AIProviderType.ANTHROPIC
        model = os.getenv("AI_MODEL", "claude-3-haiku-20240307")
    
    return AIConfig(
        provider=provider,
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        gigachat_auth_key=gigachat_key,
        gigachat_scope=gigachat_scope,
        model=model,
        temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("AI_MAX_TOKENS", "2000"))
    )


# Campaign generation prompts
CAMPAIGN_SYSTEM_PROMPT = """Ты опытный маркетолог-копирайтер, специализирующийся на контекстной рекламе.
Твоя задача — создавать высококонверсионные рекламные кампании на русском языке.

Правила:
1. Используй привлекательные заголовки с ключевыми преимуществами
2. Добавляй призывы к действию
3. Делай акцент на уникальном торговом предложении
4. Текст должен быть естественным и не содержать спама
5. Соблюдай лимиты по символам для каждой платформы

Ответ СТРОГО в JSON формате."""

CAMPAIGN_USER_PROMPT_TEMPLATE = """Создай рекламную кампанию для следующего сайта:
URL: {landing_url}

Сгенерируй:
1. Название кампании
2. 2-3 группы объявлений (по целевой аудитории или продуктам)
3. В каждой группе — 2-3 объявления с заголовком и текстом

Формат ответа:
{{
  "campaign_name": "...",
  "ad_groups": [
    {{
      "name": "...",
      "ads": [
        {{"title": "...", "text": "...", "landing_url": "{landing_url}"}}
      ]
    }}
  ]
}}"""
