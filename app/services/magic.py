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
from app.services.connector_service import get_connector

logger = logging.getLogger(__name__)
DEFAULT_AD_COUNT = 9
MAX_AD_COUNT = 50
MAX_IMAGE_COUNT = 12


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

TEXT_USER_PROMPT = """Проанализируй информацию о бизнесе и создай {ad_count} уникальных рекламных объявлений.
Сделай разные подходы: скидка, срочность, уникальность, социальное доказательство, выгода.

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

Создай {ad_count} объявлений с разнообразными подходами."""

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

    def _normalize_ad_count(self, ad_count: Optional[int]) -> int:
        try:
            count = int(ad_count) if ad_count is not None else DEFAULT_AD_COUNT
        except (TypeError, ValueError):
            count = DEFAULT_AD_COUNT
        if count < 1:
            count = DEFAULT_AD_COUNT
        return min(count, MAX_AD_COUNT)

    def _coerce_ads_count(self, ads: List[Dict[str, Any]], ad_count: int, business_info: str) -> List[Dict[str, Any]]:
        if len(ads) >= ad_count:
            return ads[:ad_count]
        fallback = self._generate_fallback_ads(business_info, ad_count).get("ads", [])
        needed = ad_count - len(ads)
        return ads + fallback[:needed]

    async def _build_business_info_with_rag(
        self,
        org_id: int,
        landing_url: str | None,
        description: str,
    ) -> str:
        business_info = description or ""
        if landing_url:
            from app.services.website_parser import WebsiteParserService

            parser = WebsiteParserService(self.db)
            scraped = await parser.parse_only(landing_url)
            if scraped:
                business_info = (
                    f"{scraped[:5000]}\n\nДополнительная информация от клиента: {description}"
                    if description
                    else scraped[:5000]
                )
                try:
                    from app.services.rag_service import RagService

                    rag = RagService(self.db)
                    await rag.ingest_text(
                        organization_id=org_id,
                        source_type="website",
                        title=landing_url,
                        url=landing_url,
                        text=scraped,
                    )
                except Exception:
                    logger.exception("RAG ingest failed for landing page")

        if not business_info.strip():
            business_info = "Универсальный бизнес, товары и услуги"

        try:
            from app.services.rag_service import RagService

            rag = RagService(self.db)
            results = await rag.search(
                organization_id=org_id,
                query=business_info,
                top_k=4,
            )
            if results:
                snippets = []
                for item in results:
                    text = item.get("text", "")
                    if text:
                        snippets.append(text[:300])
                if snippets:
                    business_info = f"{business_info}\n\nКонтекст из базы знаний:\n- " + "\n- ".join(snippets)
        except Exception:
            logger.exception("RAG search failed")

        return business_info
    
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

        return await self._generate_creatives_common(business_info, DEFAULT_AD_COUNT)

    async def generate_creatives_public(self, input_text: str, landing_url: str = None, ad_count: Optional[int] = None) -> Dict[str, Any]:
        """
        Legacy public method. 
        Note: Direct scraping is discouraged. Preferably use generate_from_context.
        """
        # If landing_url provided, try to scrape (legacy/fallback)
        business_info = input_text or ""
        
        # Собираем информацию о бизнесе
        business_info = input_text or ""
        
        if landing_url:
            from app.services.website_parser import WebsiteParserService
            parser = WebsiteParserService(self.db)
            scraped = await parser.parse_only(landing_url)
            # scraped = await scrape_landing_page(landing_url) # Legacy removed
            business_info = f"{scraped[:5000]}\n\nДополнительная информация от клиента: {input_text}" if input_text else scraped[:5000]
        
        if not business_info.strip():
            business_info = "Универсальный бизнес, товары и услуги"
        
        # ... logic ...
        return await self._generate_creatives_common(business_info, self._normalize_ad_count(ad_count))

    async def launch_magic_run(
        self,
        run_id: int,
        user_id: int,
        total_budget: int = 15000,
        platforms: List[str] = None
    ) -> Dict[str, Any]:
        """
        Convert a completed MagicRun into a real Experiment and launch it.
        """
        from app.db.models import CampaignPlan, Connection, ConnectionStatus, Platform
        from app.services.experiment_service import ExperimentService
        
        run = self.db.get(MagicRun, run_id)
        if not run:
            raise ValueError("Magic Run not found")
        
        if not run.result_json:
            raise ValueError("Magic Run has no results yet")
        
        data = run.result_json
        ads = data.get("ads", [])
        images = data.get("images", [])
        
        if not ads:
            raise ValueError("No ads generated")
            
        # 1. Create Campaign Plan
        # We need a connection. For now, pick the first active connection or create a dummy plan.
        # Ideally, user selects connection. Here we "Auto-Detect".
        connection = self.db.scalar(
            select(Connection).where(
                Connection.organization_id == run.organization_id,
                Connection.status == ConnectionStatus.active
            ).limit(1)
        )
        
        if not connection:
            # Fallback: Create plan without connection (Draft)
            # But ExperimentService needs connection to launch.
            # We can't launch without connection.
            # Check if we have MOCK mode configured or just fail?
            # User wants "Launch All". If no connection, we can't launch REAL campaign.
            pass

        # Create Plan
        plan = CampaignPlan(
            organization_id=run.organization_id,
            connection_id=connection.id if connection else None,
            name=f"Magic Campaign {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            goal="leads",
            budget=total_budget,
            status="active"
        )
        self.db.add(plan)
        self.db.commit()
        
        # 2. Create Experiment
        from app.db.models import Experiment, ExperimentStatus, ExperimentRound, Hypothesis, CreativeVariant, BudgetAllocation, ExperimentCampaign, HypothesisStatus
        from app.db.models_abtests import ABTest, ABTestVariant, ABTestStatus
        
        experiment = Experiment(
            plan_id=plan.id,
            total_budget=total_budget,
            platforms=platforms or ["yandex"], # Default to yandex if not specified
            status=ExperimentStatus.running,
            started_at=datetime.utcnow()
        )
        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)
        
        # 3. Create Round 1
        round_item = ExperimentRound(
            experiment_id=experiment.id,
            round_index=1,
            budget_plan={p: total_budget // len(experiment.platforms) for p in experiment.platforms},
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow() + timedelta(days=7),
        )
        self.db.add(round_item)
        self.db.flush()
        
        # 4. Create Assets & Launch
        # Flatten ads to launch
        target_platforms = [Platform(p) for p in (experiment.platforms or [])]
        
        # Simple Logic: Distribute ads across platforms
        # OR launch same ads on all platforms if possible.
        # Assuming ads are generic.
        
        for platform in target_platforms:
            platform_budget = round_item.budget_plan.get(platform.value, 0)
            if not ads:
                continue
                
            # Use all ads or subset? Let's use up to 5 ads.
            launch_ads = ads[:5]
            
            # Allocation
            per_ad = platform_budget // len(launch_ads)
            remainder = platform_budget % len(launch_ads)
            
            # Create Shadow ABTest
            ab_test = ABTest(
                organization_id=run.organization_id,
                name=f"Magic Exp {experiment.id} - {platform.value}",
                status=ABTestStatus.RUNNING.value,
                started_at=datetime.utcnow()
            )
            self.db.add(ab_test)
            self.db.flush()
            
            for idx, ad_data in enumerate(launch_ads):
                current_allocation = per_ad + (1 if idx < remainder else 0)
                
                # Hypothesis
                hypothesis = Hypothesis(
                    experiment_round_id=round_item.id,
                    text=f"Magic Hypothesis {idx+1}",
                    status=HypothesisStatus.active
                )
                self.db.add(hypothesis)
                self.db.flush()
                
                # Creative
                # Pick image if available
                img_data = images[idx % len(images)] if images else {}
                
                creative = CreativeVariant(
                    experiment_id=experiment.id,
                    hypothesis_id=hypothesis.id,
                    platform=platform,
                    title=ad_data.get("title", f"Title {idx}"),
                    text=ad_data.get("text", f"Text {idx}"),
                    image_url=img_data.get("url"),
                    moderation_status="approved", # Assume magic is good
                )
                self.db.add(creative)
                self.db.flush()
                
                # Budget
                self.db.add(BudgetAllocation(
                    experiment_id=experiment.id,
                    experiment_round_id=round_item.id,
                    platform=platform,
                    creative_variant_id=creative.id,
                    amount=current_allocation
                ))
                
                # Launch to Connector
                if connection and connection.platform == platform:
                    try:
                        connector = get_connector(platform, connection.credentials_json or {})
                        result = connector.create_campaign_bundle(plan, experiment, [creative])
                        c_id = result.get("campaign_id")
                        
                        if c_id:
                            self.db.add(ExperimentCampaign(
                                organization_id=run.organization_id,
                                experiment_id=experiment.id,
                                platform=platform,
                                campaign_external_id=c_id
                            ))
                            
                            # Add to ABTest
                            self.db.add(ABTestVariant(
                                ab_test_id=ab_test.id,
                                name=f"Variant {idx+1}",
                                title=creative.title,
                                text=creative.text,
                                campaign_external_id=c_id,
                                traffic_percentage=100 // len(launch_ads)
                            ))
                    except Exception as e:
                        print(f"Failed to launch magic ad on {platform}: {e}")
            
            # Common Budget bucket
            self.db.add(BudgetAllocation(
                experiment_id=experiment.id,
                experiment_round_id=round_item.id,
                platform=platform,
                creative_variant_id=None,
                amount=0 
            ))

        self.db.commit()
        
        return {"experiment_id": experiment.id, "message": f"Launched {len(ads)} ads on {len(target_platforms)} platforms!"}
        
        return await self._generate_creatives_common(business_info, self._normalize_ad_count(ad_count))

    async def _generate_creatives_common(self, business_info: str, ad_count: int) -> Dict[str, Any]:
        # Генерируем тексты объявлений
        ads_result = await self._generate_ad_texts(business_info, ad_count)
        
        # Генерируем изображения
        images_result = await self._generate_images(
            ads_result.get("business_type", "бизнес"),
            ads_result.get("ads", []),
            ad_count
        )
        
        return {
            "business_name": ads_result.get("business_name", "Бизнес"),
            "business_type": ads_result.get("business_type", "услуги"),
            "ads": ads_result.get("ads", []),
            "images": images_result
        }
    
    async def _generate_ad_texts(self, business_info: str, ad_count: int) -> Dict[str, Any]:
        """Generate ad text variations."""
        ad_count = self._normalize_ad_count(ad_count)
        prompt = TEXT_USER_PROMPT.format(business_info=business_info, ad_count=ad_count)
        
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
                    result = self._generate_fallback_ads(business_info, ad_count)

            if not isinstance(result, dict):
                result = self._generate_fallback_ads(business_info, ad_count)

            ads = result.get("ads") or []
            if not isinstance(ads, list):
                ads = []
            ads = self._coerce_ads_count(ads, ad_count, business_info)
            result["ads"] = ads
            result.setdefault("business_name", "Бизнес")
            result.setdefault("business_type", "услуги")
            return result
            
        except Exception as e:
            logger.exception("Text generation failed")
            return self._generate_fallback_ads(business_info, ad_count)
    
    def _generate_fallback_ads(self, business_info: str, ad_count: int = DEFAULT_AD_COUNT) -> Dict[str, Any]:
        """Fallback ads when AI fails."""
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

        ads = []
        for i in range(self._normalize_ad_count(ad_count)):
            template = templates[i % len(templates)]
            ads.append({**template})

        return {
            "business_name": "Бизнес",
            "business_type": "услуги",
            "ads": ads
        }
    
    async def _generate_images(self, business_type: str, ads: List[Dict], count: int) -> List[Dict[str, str]]:
        """Generate image creatives."""
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

        total = min(self._normalize_ad_count(count), MAX_IMAGE_COUNT)
        for i in range(total):
            ad_theme = None
            if i < len(ads):
                ad_theme = ads[i].get("theme") or ads[i].get("approach")
            theme = ad_theme or themes[i % len(themes)]
            prompt = IMAGE_PROMPT_TEMPLATE.format(business_type=business_type, theme=theme)
            
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
            input_data = run.input_json or {}
            landing_url = input_data.get('landing_url')
            description = input_data.get('description', '')
            ad_count = self._normalize_ad_count(input_data.get("ad_count"))

            business_info = await self._build_business_info_with_rag(
                run.organization_id,
                landing_url,
                description,
            )
            result = await self._generate_creatives_common(business_info, ad_count)
            drafts = self._create_drafts(run, result)
            result["drafts"] = drafts
            result["ad_count"] = ad_count
            run.result_json = result
            run.status = "success"
            
            # Create Draft Entities
            # Drafts already created in _create_drafts
            
        except Exception as e:
            logger.exception("Magic Run Failed")
            run.error = str(e)
            run.status = "failed"
        
        self.db.commit()
    
    def _create_drafts(self, run: MagicRun, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create DraftCampaigns with ads from generation result."""
        ads = result.get("ads", []) or []
        images = result.get("images", []) or []
        input_data = run.input_json or {}

        budget = input_data.get("budget_daily") or input_data.get("budget_total") or 1000
        landing_url = input_data.get("landing_url", "")
        product_ids = input_data.get("product_ids", []) or []

        connection_ids = input_data.get("connection_ids") or []
        if input_data.get("connection_id") and not connection_ids:
            connection_ids = [input_data.get("connection_id")]
        if connection_ids:
            seen = set()
            connection_ids = [cid for cid in connection_ids if not (cid in seen or seen.add(cid))]

        drafts_info: List[Dict[str, Any]] = []

        def create_draft(platform: str, connection_id: int | None) -> DraftCampaign:
            name_suffix = platform.upper()
            campaign = DraftCampaign(
                organization_id=run.organization_id,
                connection_id=connection_id,
                magic_run_id=run.id,
                platform=platform,
                name=f"Magic: {result.get('business_name', 'Кампания')} ({name_suffix})",
                status="draft",
                payload_json={
                    "budget": budget,
                    "landing_url": landing_url,
                    "campaign_goal": input_data.get("campaign_goal"),
                    "target_audience": input_data.get("target_audience"),
                    "product_ids": product_ids,
                },
            )
            self.db.add(campaign)
            self.db.flush()

            group = DraftAdGroup(
                campaign_id=campaign.id,
                name="Основная группа объявлений",
                payload_json={"keywords": input_data.get("keywords", [])},
            )
            self.db.add(group)
            self.db.flush()

            ads_for_platform = ads

            for i, ad_data in enumerate(ads_for_platform):
                image_url = images[i]["url"] if i < len(images) else None
                ad = DraftAd(
                    ad_group_id=group.id,
                    title=ad_data.get("title", ""),
                    text=ad_data.get("text", ""),
                    landing_url=landing_url,
                    payload_json={
                        "approach": ad_data.get("approach", ""),
                        "image_url": image_url,
                    },
                )
                self.db.add(ad)

            return campaign

        if connection_ids:
            from app.db.models import Connection

            connections = (
                self.db.query(Connection)
                .filter(Connection.id.in_(connection_ids))
                .all()
            )
            conn_map = {conn.id: conn for conn in connections}
            for conn_id in connection_ids:
                connection = conn_map.get(conn_id)
                if not connection:
                    continue
                platform = connection.platform.value if hasattr(connection.platform, "value") else str(connection.platform)
                campaign = create_draft(platform, connection.id)
                drafts_info.append({
                    "id": campaign.id,
                    "platform": platform,
                    "connection_id": connection.id,
                })
            return drafts_info

        platform = input_data.get("platform", "yandex")
        campaign = create_draft(platform, input_data.get("connection_id"))
        drafts_info.append({
            "id": campaign.id,
            "platform": platform,
            "connection_id": input_data.get("connection_id"),
        })
        return drafts_info
    
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
