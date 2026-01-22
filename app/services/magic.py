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

# =============================================================================
# WEB SCRAPER (с глубоким анализом)
# =============================================================================

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

async def scrape_landing_page(url: str) -> str:
    """
    Глубокий анализ сайта: главная + 2 внутренние страницы.
    Использует BeautifulSoup для качественного извлечения текста.
    """
    max_pages = 3
    visited_urls = set()
    collected_content = []
    
    # Очередь для обхода: (url, depth)
    queue = [(url, 0)]
    
    domain = urlparse(url).netloc
    base_url = url
    
    logger.info(f"Starting deep scrape for: {url}")
    
    if not url.startswith("http"):
        url = f"https://{url}"
    
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (compatible; AI-Ad-Generator/1.0)"}) as client:
        while queue and len(visited_urls) < max_pages:
            current_url, depth = queue.pop(0)
            
            if current_url in visited_urls:
                continue
                
            visited_urls.add(current_url)
            
            try:
                response = await client.get(current_url)
                response.raise_for_status()
                html = response.text
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Удаляем мусор
                for script in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
                    script.extract()
                
                # Извлекаем мета-данные (только с главной)
                if depth == 0:
                    title = soup.title.string.strip() if soup.title and soup.title.string else ""
                    desc_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
                    description = desc_tag.get('content', '').strip() if desc_tag else ""
                    
                    collected_content.append(f"ГЛАВНАЯ СТРАНИЦА:\nЗаголовок: {title}\nОписание: {description}\n")
                
                # Извлекаем основной текст
                # Приоритет контентным тегам
                text_blocks = []
                for tag in ['h1', 'h2', 'h3', 'p', 'li', 'article', 'section']:
                    for el in soup.find_all(tag):
                        text = el.get_text(strip=True)
                        if text and len(text) > 20: # Игнорируем совсем короткие фразы
                            text_blocks.append(text)
                
                # Уникализируем и объединяем
                page_text = "\n".join(list(dict.fromkeys(text_blocks))[:30]) # Берём топ-30 уникальных блоков
                collected_content.append(f"--- Контент со страницы {current_url} ---\n{page_text[:1500]}\n")
                
                # Ищем внутренние ссылки (только на глубине 0)
                if depth == 0:
                    links = []
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        full_url = urljoin(current_url, href)
                        parsed = urlparse(full_url)
                        
                        # Фильтруем ссылки: только тот же домен, не файлы, не якоря
                        if parsed.netloc == domain and full_url not in visited_urls:
                            if any(ext in parsed.path.lower() for ext in ['.pdf', '.jpg', '.png', '.zip', '.css', '.js']):
                                continue
                            if '#' in href:
                                continue
                                
                            # Приоритет полезным страницам
                            score = 0
                            if any(w in full_url.lower() for w in ['about', 'company', 'uslugi', 'service', 'price', 'contact', 'о-нас', 'цены', 'услуги']):
                                score = 10
                            
                            links.append((score, full_url))
                    
                    # Сортируем по важности и добавляем топ-3 в очередь
                    links.sort(key=lambda x: x[0], reverse=True)
                    for _, link in links[:max_pages-1]:
                        if link not in [q[0] for q in queue]:
                            queue.append((link, depth + 1))
                            
            except Exception as e:
                logger.warning(f"Error scraping {current_url}: {e}")
                
    result = "\n".join(collected_content)
    if not result:
        return f"Не удалось извлечь данные с {url}"
        
    return result[:8000] # Ограничиваем общий объем текста


# =============================================================================
# MAGIC SERVICE
# =============================================================================

class MagicService:
    """AI-powered ad creative generation service."""
    
    def __init__(self, db: Session, text_provider: TextProvider = None, image_provider: ImageProvider = None):
        self.db = db
        self.text_ai = text_provider or get_text_provider()
        # Use DALL-E if API key available, otherwise mock
        if image_provider:
            self.image_ai = image_provider
        else:
            import os
            if os.getenv("OPENAI_API_KEY"):
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
    
    async def generate_from_context(self, context_id: int, input_text: str = "") -> Dict[str, Any]:
        """
        Generates creatives using pre-parsed BusinessContext.
        """
        from app.db.models_context import BusinessContext
        context = self.db.get(BusinessContext, context_id)
        if not context or not context.clean_text:
             raise ValueError("Context not found or empty")

        # Construct rich info from context
        business_info = (
            f"URL: {context.url}\n"
            f"Title: {context.meta_title}\n"
            f"Description: {context.meta_description}\n"
            f"Content Summary:\n{context.clean_text[:5000]}\n"
        )
        if input_text:
             business_info += f"\nAdditional User Info: {input_text}"

        return await self._generate_creatives_common(business_info)

    async def generate_creatives_public(self, input_text: str, landing_url: str = None) -> Dict[str, Any]:
        """
        Legacy public method. 
        Note: Direct scraping is discouraged. Preferably use generate_from_context.
        """
        # If landing_url provided, try to scrape (legacy/fallback)
        business_info = input_text or ""
        
        if landing_url:
             # Just use what we have, skip deep scrape here to force using the Parser Service + Context flow
             # Or keep legacy behavior? 
             # Let's keep legacy but simplified or warn.
             # Ideally we should call WebsiteParserService here but we don't have org_id easily for public.
             # For now, we reuse the old scrape logic if simpler, OR better:
             # We rely on text input mostly.
             pass

        if not business_info.strip():
            business_info = "Универсальный бизнес, товары и услуги"
        
        return await self._generate_creatives_common(business_info)

    async def _generate_creatives_common(self, business_info: str) -> Dict[str, Any]:
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
        """Generate 10 image creatives."""
        images = []
        
        themes = [
            "главный продукт или услуга",
            "довольный клиент",
            "команда профессионалов",
            "процесс работы",
            "результат услуги",
            "офис или магазин",
            "акция и скидки",
            "качество и надёжность",
            "быстрая доставка",
            "контакты и связь"
        ]
        
        for i, theme in enumerate(themes):
            prompt = IMAGE_PROMPT_TEMPLATE.format(
                business_type=business_type,
                theme=theme
            )
            
            try:
                image_url = await self.image_ai.generate_image(prompt)
                images.append({
                    "url": image_url,
                    "prompt": prompt,
                    "theme": theme
                })
            except Exception as e:
                logger.warning(f"Image generation failed for theme {theme}: {e}")
                # Placeholder image
                images.append({
                    "url": f"https://picsum.photos/seed/{i+1}/400/400",
                    "prompt": prompt,
                    "theme": theme
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
        
        # Create ads
        landing_url = run.input_json.get("landing_url", "")
        
        for i, ad_data in enumerate(ads):
            image_url = images[i]["url"] if i < len(images) else None
            
            ad = DraftAd(
                ad_group_id=group.id,
                title=ad_data.get("title", ""),
                text=ad_data.get("text", ""),
                landing_url=landing_url,
                payload_json={
                    "approach": ad_data.get("approach", ""),
                    "image_url": image_url
                }
            )
            self.db.add(ad)
    
    def create_drafts_from_public(self, org_id: int, user_id: int, creatives: Dict[str, Any], landing_url: str = "") -> DraftCampaign:
        """
        Create draft campaign from publicly generated creatives.
        Called after user registration.
        """
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
            
            ad = DraftAd(
                ad_group_id=group.id,
                title=ad_data.get("title", ""),
                text=ad_data.get("text", ""),
                landing_url=landing_url,
                payload_json={
                    "approach": ad_data.get("approach", ""),
                    "image_url": image_url
                }
            )
            self.db.add(ad)
        
        self.db.commit()
        self.db.refresh(campaign)
        return campaign
