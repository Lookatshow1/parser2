"""
Magic Service - AI-Powered Ad Creative Generation

Generates selling ad texts and images from a URL or business description.
"""
import json
import logging
import re
import httpx
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.db.models_magic import MagicRun
from app.db.models_drafts import DraftCampaign, DraftAdGroup, DraftAd
from app.core.ai.interfaces import TextProvider, ImageProvider
from app.core.ai.openai_provider import get_text_provider
from app.core.ai.dalle_provider import DalleProvider, get_dalle_provider
from app.core.ai.mock_provider import MockImageProvider
from app.core.ai.nanobanana_provider import NanoBananaProvider, get_nanobanana_provider

logger = logging.getLogger(__name__)


# =============================================================================
# ПРОДАЮЩИЕ ПРОМПТЫ
# =============================================================================

TEXT_SYSTEM_PROMPT = """Ты — эксперт по контекстной рекламе с 15-летним опытом. 
Ты создаёшь продающие объявления для Яндекс Директ, которые привлекают клики и конверсии.

Правила:
- Заголовок: до 35 символов, цепляющий, с выгодой
- Текст: до 81 символа, призыв к действию
- Используй разные подходы: скидка, срочность, уникальность, социальное доказательство
- Пиши на русском языке
- Без кавычек в начале и конце"""

TEXT_USER_PROMPT = """Проанализируй информацию о бизнесе и создай 9 уникальных рекламных объявлений.
Для каждой ключевой темы создай 3 A/B варианта с разными подходами.

ИНФОРМАЦИЯ О БИЗНЕСЕ:
{business_info}

Верни JSON в формате:
{{
  "business_name": "название бизнеса",
  "business_type": "тип бизнеса (одежда, услуги, еда и т.д.)",
  "ads": [
    {{
      "title": "Заголовок до 35 символов",
      "text": "Текст до 81 символа с призывом",
      "approach": "emotional|rational|usp",
      "variant_group": "A|B|C",
      "theme": "основная тема объявления"
    }}
  ]
}}

Подходы:
- emotional: эмоциональный, вызывающий чувства
- rational: рациональный, с фактами и цифрами  
- usp: уникальное торговое предложение

Создай 9 объявлений: 3 темы × 3 варианта (A, B, C) с разными подходами."""

IMAGE_PROMPT_TEMPLATE = """Создай рекламный баннер для {business_type}:
- Тема: {theme}
- Стиль: современный, минималистичный, профессиональный
- Цвета: яркие, привлекающие внимание
- Формат: квадратный баннер для рекламы
- Без текста на изображении
- Фотореалистичный или высококачественная графика"""


# =============================================================================
# WEB SCRAPER (для анализа URL)
# =============================================================================

async def scrape_landing_page(url: str) -> str:
    """Извлекает текст с лендинга для анализа."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            html = response.text
            
            # Простое извлечение текста (без BeautifulSoup для минимизации зависимостей)
            # Удаляем скрипты и стили
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            
            # Извлекаем title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""
            
            # Извлекаем meta description
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Извлекаем h1, h2, h3
            headings = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html, re.IGNORECASE | re.DOTALL)
            headings_text = " ".join([re.sub(r'<[^>]+>', '', h).strip() for h in headings[:5]])
            
            # Извлекаем параграфы
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
            paragraphs_text = " ".join([re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs[:10]])
            
            result = f"""
URL: {url}
Заголовок: {title}
Описание: {description}
Заголовки страницы: {headings_text}
Контент: {paragraphs_text[:500]}
"""
            return result.strip()
            
    except Exception as e:
        logger.warning(f"Failed to scrape {url}: {e}")
        return f"URL: {url} (не удалось загрузить страницу)"


# =============================================================================
# MAGIC SERVICE
# =============================================================================

class MagicService:
    """AI-powered ad creative generation service."""
    
    def __init__(self, db: Session, text_provider: TextProvider = None, image_provider: ImageProvider = None):
        self.db = db
        self.text_ai = text_provider or get_text_provider()
        # Image provider priority: NanoBanana > DALL-E > Mock
        if image_provider:
            self.image_ai = image_provider
        else:
            import os
            # Prefer NanoBanana for marketing banners with text
            if os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY"):
                self.image_ai = get_nanobanana_provider()
            elif os.getenv("OPENAI_API_KEY"):
                self.image_ai = get_dalle_provider()
            else:
                self.image_ai = MockImageProvider()
    
    async def create_magic_run(self, org_id: int, user_id: int, input_data: dict) -> MagicRun:
        """Create a new magic run record."""
        run = MagicRun(
            organization_id=org_id,
            created_by_user_id=user_id,
            status="pending",
            input_json=input_data
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
    
    async def generate_creatives_public(self, input_text: str, landing_url: str = None) -> Dict[str, Any]:
        """
        Публичный метод для генерации креативов БЕЗ авторизации.
        Используется на главной странице.
        
        Returns:
            {
                "business_name": str,
                "business_type": str,
                "ads": [{"title": str, "text": str, "approach": str}, ...],
                "images": [{"url": str, "prompt": str}, ...]
            }
        """
        # Собираем информацию о бизнесе
        business_info = input_text or ""
        
        if landing_url:
            scraped = await scrape_landing_page(landing_url)
            business_info = f"{scraped}\n\nДополнительная информация от клиента: {input_text}" if input_text else scraped
        
        if not business_info.strip():
            business_info = "Универсальный бизнес, товары и услуги"
        
        # Генерируем тексты объявлений
        ads_result = await self._generate_ad_texts(business_info)
        
        # Генерируем изображения
        images_result = await self._generate_images(
            ads_result.get("business_type", "бизнес"),
            ads_result.get("ads", [])
        )
        
        return {
            "business_name": ads_result.get("business_name", "Бизнес"),
            "business_type": ads_result.get("business_type", "услуги"),
            "ads": ads_result.get("ads", []),
            "images": images_result
        }
    
    async def _generate_ad_texts(self, business_info: str) -> Dict[str, Any]:
        """Generate 10 ad text variations."""
        prompt = TEXT_USER_PROMPT.format(business_info=business_info)
        
        try:
            result = await self.text_ai.generate_text(
                prompt,
                system_prompt=TEXT_SYSTEM_PROMPT,
                json_schema={
                    "type": "object",
                    "properties": {
                        "business_name": {"type": "string"},
                        "business_type": {"type": "string"},
                        "ads": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "text": {"type": "string"},
                                    "approach": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            )
            
            if isinstance(result, str):
                # Try to parse JSON from string
                try:
                    result = json.loads(result)
                except:
                    result = self._generate_fallback_ads(business_info)
            
            return result
            
        except Exception as e:
            logger.exception("Text generation failed")
            return self._generate_fallback_ads(business_info)
    
    def _generate_fallback_ads(self, business_info: str) -> Dict[str, Any]:
        """Fallback ads when AI fails."""
        approaches = ["скидка", "срочность", "уникальность", "доверие", "выгода"]
        ads = []
        
        templates = [
            {"title": "Скидка 30% только сегодня!", "text": "Успейте заказать со скидкой. Доставка бесплатно!", "approach": "скидка"},
            {"title": "Осталось 5 мест", "text": "Успейте записаться сегодня. Звоните прямо сейчас!", "approach": "срочность"},
            {"title": "№1 в своей нише", "text": "Лидер рынка с 2010 года. Гарантия качества!", "approach": "уникальность"},
            {"title": "10 000+ довольных клиентов", "text": "Присоединяйтесь к тем, кто уже с нами. Отзывы 5.0", "approach": "доверие"},
            {"title": "Экономьте до 50%", "text": "Лучшие цены на рынке. Сравните сами!", "approach": "выгода"},
            {"title": "Бесплатная консультация", "text": "Эксперт ответит на все вопросы. Оставьте заявку!", "approach": "выгода"},
            {"title": "Акция до конца недели", "text": "Специальное предложение для новых клиентов!", "approach": "срочность"},
            {"title": "Качество проверено временем", "text": "Работаем для вас уже 10 лет. Надёжность!", "approach": "доверие"},
            {"title": "Только у нас", "text": "Эксклюзивные условия для наших клиентов!", "approach": "уникальность"},
            {"title": "Подарок при заказе", "text": "Сделайте заказ сегодня и получите бонус!", "approach": "скидка"},
        ]
        
        return {
            "business_name": "Бизнес",
            "business_type": "услуги",
            "ads": templates
        }
    
    async def _generate_images(self, business_type: str, ads: List[Dict]) -> List[Dict[str, str]]:
        """Generate marketing banners with ad headlines."""
        images = []
        
        # Generate banners for each ad, using headlines for text
        for i, ad in enumerate(ads[:10]):  # Limit to 10 banners
            headline = ad.get("title", "")
            subline = ad.get("text", "")[:40] + "..." if len(ad.get("text", "")) > 40 else ad.get("text", "")
            approach = ad.get("approach", "modern")
            
            # Map approach to visual style
            style_map = {
                "emotional": "bold",
                "rational": "minimal",
                "usp": "tech",
                "скидка": "bold",
                "срочность": "bold",
                "уникальность": "premium",
                "доверие": "minimal",
                "выгода": "modern"
            }
            style = style_map.get(approach, "modern")
            
            try:
                # Try NanoBanana for marketing banners
                if hasattr(self.image_ai, 'generate_banner'):
                    image_url = await self.image_ai.generate_banner(
                        headline=headline,
                        subline=subline,
                        business_type=business_type,
                        style=style
                    )
                else:
                    # Fallback to regular image generation
                    prompt = IMAGE_PROMPT_TEMPLATE.format(
                        business_type=business_type,
                        theme=headline
                    )
                    image_url = await self.image_ai.generate_image(prompt)
                
                images.append({
                    "url": image_url,
                    "headline": headline,
                    "subline": subline,
                    "theme": approach,
                    "prompt": f"Banner for {business_type}: {headline}"
                })
            except Exception as e:
                logger.warning(f"Image generation failed for ad {i}: {e}")
                # Placeholder with business-related seed
                images.append({
                    "url": f"https://picsum.photos/seed/{hash(headline) % 1000}/400/400",
                    "headline": headline,
                    "subline": subline,
                    "theme": approach,
                    "prompt": f"Placeholder for: {headline}"
                })
        
        return images
    
    async def process_run(self, run_id: int):
        """Execute the AI generation pipeline for authenticated users."""
        run = self.db.query(MagicRun).filter(MagicRun.id == run_id).first()
        if not run:
            return
        
        run.status = "running"
        self.db.commit()
        
        try:
            # Get business info
            landing_url = run.input_json.get('landing_url')
            description = run.input_json.get('description', '')
            
            # Generate creatives
            result = await self.generate_creatives_public(description, landing_url)
            
            run.result_json = result
            run.status = "success"
            
            # Create Draft Entities
            self._create_drafts(run, result)
            
        except Exception as e:
            logger.exception("Magic Run Failed")
            run.error = str(e)
            run.status = "failed"
        
        self.db.commit()
    
    def _create_drafts(self, run: MagicRun, result: Dict[str, Any]):
        """Create DraftCampaign with ads from generation result."""
        from app.services.magic_launch import generate_erid
        
        ads = result.get("ads", [])
        images = result.get("images", [])
        
        campaign = DraftCampaign(
            organization_id=run.organization_id,
            connection_id=run.input_json.get("connection_id"),
            magic_run_id=run.id,
            platform=run.input_json.get("platform", "yandex"),
            name=f"Magic: {result.get('business_name', 'Кампания')}",
            status="draft",
            payload_json={"budget": run.input_json.get("budget", 1000)}
        )
        self.db.add(campaign)
        self.db.flush()
        
        # Create ad group
        group = DraftAdGroup(
            campaign_id=campaign.id,
            name="Основная группа объявлений",
            payload_json={"keywords": run.input_json.get("keywords", [])}
        )
        self.db.add(group)
        self.db.flush()
        
        # Create ads with ERID
        landing_url = run.input_json.get("landing_url", "")
        
        for i, ad_data in enumerate(ads):
            image_url = images[i]["url"] if i < len(images) else None
            # Generate ERID for each ad (ФЗ "О рекламе")
            erid = generate_erid()
            
            ad = DraftAd(
                ad_group_id=group.id,
                title=ad_data.get("title", ""),
                text=ad_data.get("text", ""),
                erid=erid,
                landing_url=landing_url,
                payload_json={
                    "approach": ad_data.get("approach", ""),
                    "image_url": image_url,
                    "erid": erid
                }
            )
            self.db.add(ad)
    
    def create_drafts_from_public(self, org_id: int, user_id: int, creatives: Dict[str, Any], landing_url: str = "") -> DraftCampaign:
        """
        Create draft campaign from publicly generated creatives.
        Called after user registration.
        """
        from app.services.magic_launch import generate_erid
        
        ads = creatives.get("ads", [])
        images = creatives.get("images", [])
        
        campaign = DraftCampaign(
            organization_id=org_id,
            platform="yandex",
            name=f"Magic: {creatives.get('business_name', 'Новая кампания')}",
            status="draft",
            payload_json={"budget": 1000}
        )
        self.db.add(campaign)
        self.db.flush()
        
        group = DraftAdGroup(
            campaign_id=campaign.id,
            name="Основная группа",
            payload_json={}
        )
        self.db.add(group)
        self.db.flush()
        
        for i, ad_data in enumerate(ads):
            image_url = images[i]["url"] if i < len(images) else None
            # Generate ERID for compliance (ФЗ "О рекламе")
            erid = generate_erid()
            
            ad = DraftAd(
                ad_group_id=group.id,
                title=ad_data.get("title", ""),
                text=ad_data.get("text", ""),
                erid=erid,
                landing_url=landing_url,
                payload_json={
                    "approach": ad_data.get("approach", ""),
                    "image_url": image_url,
                    "erid": erid
                }
            )
            self.db.add(ad)
        
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

