"""
Creative AI Studio.

Advanced AI-powered creative generation:
- Bulk variations generation
- Style transfer
- Creative performance prediction
- A/B test recommendations
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import json
import re

from app.core.ai.openai_provider import get_text_provider
from app.core.ai.dalle_provider import DalleProvider

logger = logging.getLogger(__name__)


@dataclass
class CreativeVariation:
    """Generated creative variation."""
    id: str
    title: str
    text: str
    approach: str
    predicted_ctr: Optional[float] = None
    predicted_cvr: Optional[float] = None
    confidence: Optional[float] = None
    image_prompt: Optional[str] = None
    image_url: Optional[str] = None


@dataclass
class CreativeBundle:
    """Bundle of creative variations."""
    original_title: str
    original_text: str
    variations: List[CreativeVariation]
    generated_at: datetime


class CreativeStudio:
    """
    AI Creative Studio for generating high-converting ad creatives.
    """
    
    APPROACHES = [
        "urgency",         # Срочность
        "scarcity",        # Дефицит
        "social_proof",    # Социальное доказательство
        "authority",       # Авторитет
        "benefit_focused", # Фокус на выгоде
        "problem_solution",# Проблема-решение
        "comparison",      # Сравнение
        "emotional",       # Эмоциональный
        "rational",        # Рациональный
        "curiosity",       # Любопытство
    ]
    
    def __init__(self):
        self.text_provider = get_text_provider()
        self.image_provider = DalleProvider()
    
    async def generate_variations(
        self,
        original_title: str,
        original_text: str,
        count: int = 50,
        target_platform: str = "yandex",
        business_context: Optional[str] = None,
    ) -> CreativeBundle:
        """
        Generate multiple variations of a creative.
        
        Args:
            original_title: Base headline
            original_text: Base ad text
            count: Number of variations (up to 100)
            target_platform: Platform for size limits
            business_context: Additional business info
        """
        # Get platform constraints
        constraints = self._get_platform_constraints(target_platform)
        
        prompt = f"""
Ты — эксперт по рекламным креативам с 15-летним опытом.

ИСХОДНЫЙ КРЕАТИВ:
Заголовок: {original_title}
Текст: {original_text}
Бизнес: {business_context or 'не указан'}

ЗАДАЧА:
Создай {count} уникальных вариаций этого объявления.

ОГРАНИЧЕНИЯ ({target_platform}):
- Заголовок: до {constraints['title_length']} символов
- Текст: до {constraints['text_length']} символов

ПОДХОДЫ (используй разные):
1. Срочность (urgency) — ограниченное время/количество
2. Дефицит (scarcity) — осталось мало
3. Социальное доказательство (social_proof) — отзывы, клиенты
4. Авторитет (authority) — эксперты, сертификаты
5. Выгода (benefit_focused) — что получит клиент
6. Проблема-решение (problem_solution) — боль → решение
7. Сравнение (comparison) — лучше чем X
8. Эмоции (emotional) — чувства, мечты
9. Логика (rational) — факты, цифры
10. Любопытство (curiosity) — интрига

Верни JSON:
{{
  "variations": [
    {{
      "id": "v1",
      "title": "заголовок",
      "text": "текст объявления",
      "approach": "подход из списка"
    }}
  ]
}}

Каждая вариация должна быть УНИКАЛЬНОЙ и использовать разные подходы.
"""
        
        try:
            response = await self.text_provider.generate_text(prompt=prompt)
            
            # Parse JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                raise ValueError("No JSON in response")
            
            data = json.loads(json_match.group())
            variations_data = data.get("variations", [])
            
            variations = []
            for v in variations_data:
                variations.append(CreativeVariation(
                    id=v.get("id", f"v{len(variations)+1}"),
                    title=v.get("title", "")[:constraints['title_length']],
                    text=v.get("text", "")[:constraints['text_length']],
                    approach=v.get("approach", "benefit_focused"),
                ))
            
            return CreativeBundle(
                original_title=original_title,
                original_text=original_text,
                variations=variations,
                generated_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.exception(f"Error generating variations: {e}")
            return CreativeBundle(
                original_title=original_title,
                original_text=original_text,
                variations=[],
                generated_at=datetime.utcnow(),
            )
    
    async def predict_performance(
        self,
        title: str,
        text: str,
        industry: str,
        target_audience: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Predict performance metrics for a creative.
        
        Returns predicted CTR, CVR with confidence scores.
        """
        prompt = f"""
Оцени потенциальную эффективность рекламного объявления.

ОБЪЯВЛЕНИЕ:
Заголовок: {title}
Текст: {text}
Отрасль: {industry}
Аудитория: {target_audience or 'широкая'}

Оцени по шкале 0-100:
1. Привлекательность заголовка (title_score)
2. Убедительность текста (text_score)
3. Призыв к действию (cta_score)
4. Релевантность аудитории (relevance_score)
5. Эмоциональный отклик (emotion_score)

Предскажи метрики:
- predicted_ctr: ожидаемый CTR в %
- predicted_cvr: ожидаемый CVR в %
- confidence: уверенность в прогнозе (0-1)

Верни JSON:
{{
  "title_score": 75,
  "text_score": 80,
  "cta_score": 70,
  "relevance_score": 85,
  "emotion_score": 65,
  "predicted_ctr": 2.5,
  "predicted_cvr": 3.0,
  "confidence": 0.7,
  "recommendations": ["рекомендация 1", "рекомендация 2"]
}}
"""
        
        try:
            response = await self.text_provider.generate_text(prompt=prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            logger.exception(f"Error predicting performance: {e}")
            return {}
    
    async def generate_image_prompts(
        self,
        title: str,
        text: str,
        business_type: str,
        count: int = 5,
    ) -> List[str]:
        """Generate DALL-E prompts for ad images."""
        prompt = f"""
Создай {count} промптов для генерации рекламных изображений (DALL-E).

ОБЪЯВЛЕНИЕ:
Заголовок: {title}
Текст: {text}
Тип бизнеса: {business_type}

ТРЕБОВАНИЯ К ПРОМПТАМ:
- Профессиональное качество
- Подходит для рекламы
- Без текста на изображении
- Современный стиль
- На английском языке

Верни JSON:
{{
  "prompts": ["prompt 1", "prompt 2", ...]
}}
"""
        
        try:
            response = await self.text_provider.generate_text(prompt=prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("prompts", [])
            return []
        except Exception as e:
            logger.exception(f"Error generating image prompts: {e}")
            return []
    
    async def analyze_creative_performance(
        self,
        creatives: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Analyze why certain creatives perform better than others.
        
        Args:
            creatives: List of {title, text, ctr, cvr, impressions}
        """
        # Sort by CTR
        sorted_creatives = sorted(creatives, key=lambda x: x.get("ctr", 0), reverse=True)
        
        top_performers = sorted_creatives[:5]
        low_performers = sorted_creatives[-5:]
        
        prompt = f"""
Проанализируй, почему одни креативы работают лучше других.

ТОП-ПЕРФОРМЕРЫ:
{json.dumps(top_performers, ensure_ascii=False, indent=2)}

СЛАБЫЕ КРЕАТИВЫ:
{json.dumps(low_performers, ensure_ascii=False, indent=2)}

Выяви паттерны и дай рекомендации.

Верни JSON:
{{
  "winning_patterns": ["что делает креативы успешными..."],
  "common_mistakes": ["частые ошибки..."],
  "word_analysis": {{
    "high_ctr_words": ["слова из успешных"],
    "low_ctr_words": ["слова из неудачных"]
  }},
  "recommendations": ["конкретные рекомендации..."]
}}
"""
        
        try:
            response = await self.text_provider.generate_text(prompt=prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            logger.exception(f"Error analyzing creatives: {e}")
            return {}
    
    async def suggest_ab_tests(
        self,
        title: str,
        text: str,
    ) -> List[Dict[str, Any]]:
        """Suggest A/B test hypotheses for a creative."""
        prompt = f"""
Предложи A/B тесты для креатива:

Заголовок: {title}
Текст: {text}

Верни 5 гипотез для тестирования:

{{
  "tests": [
    {{
      "hypothesis": "описание гипотезы",
      "original": "текущий вариант элемента",
      "variant": "тестовый вариант",
      "element": "title/text/cta",
      "expected_lift": "ожидаемый прирост в %"
    }}
  ]
}}
"""
        
        try:
            response = await self.text_provider.generate_text(prompt=prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("tests", [])
            return []
        except Exception as e:
            logger.exception(f"Error suggesting tests: {e}")
            return []
    
    def _get_platform_constraints(self, platform: str) -> Dict[str, int]:
        """Get character limits for platform."""
        constraints = {
            "yandex": {"title_length": 35, "text_length": 81},
            "vk": {"title_length": 33, "text_length": 220},
            "ozon": {"title_length": 200, "text_length": 500},
            "google": {"title_length": 30, "text_length": 90},
        }
        return constraints.get(platform, constraints["yandex"])
    
    async def close(self):
        """Close providers."""
        await self.image_provider.close()
