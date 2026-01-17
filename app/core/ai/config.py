"""
AI Provider Configuration

This module provides configuration for AI providers.
Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables to enable.
"""
import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class AIProviderType(str, Enum):
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIConfig(BaseModel):
    provider: AIProviderType = AIProviderType.MOCK
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000


def get_ai_config() -> AIConfig:
    """
    Get AI configuration from environment variables.
    Automatically detects available providers.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Auto-detect provider based on available keys
    provider = AIProviderType.MOCK
    if openai_key:
        provider = AIProviderType.OPENAI
    elif anthropic_key:
        provider = AIProviderType.ANTHROPIC
    
    return AIConfig(
        provider=provider,
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        model=os.getenv("AI_MODEL", "gpt-4o-mini"),
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
