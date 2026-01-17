"""
Platform-specific AI generation strategies.

Each platform has unique requirements for ad creatives:
- Yandex Direct: Multi-page scanning, search + display ads
- Ozon: Product cards, marketplace-specific formats
- VK Ads: Social-first, visual-heavy creatives
- Google Ads: Search + Display + YouTube
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import httpx
import re

# Optional BeautifulSoup import with fallback
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None


@dataclass
class ScannedPage:
    """Scanned page data."""
    url: str
    title: str
    description: str
    keywords: List[str]
    headings: List[str]
    content_snippets: List[str]
    images: List[str]
    products: List[Dict[str, Any]]  # For e-commerce


class PlatformStrategy(ABC):
    """Base class for platform-specific generation strategies."""
    
    platform_name: str = "generic"
    
    @abstractmethod
    async def scan_and_analyze(self, landing_url: str) -> Dict[str, Any]:
        """Scan landing page and extract relevant data for this platform."""
        pass
    
    @abstractmethod
    def build_generation_prompt(self, analysis: Dict[str, Any], description: str) -> str:
        """Build platform-specific prompt for AI generation."""
        pass
    
    @abstractmethod
    def get_ad_formats(self) -> List[str]:
        """Return list of ad formats for this platform."""
        pass


class YandexDirectStrategy(PlatformStrategy):
    """
    Yandex Direct Strategy.
    
    Features:
    - Multi-page scanning (main + relevant subpages)
    - Search ads: Title + Body + Sitelinks
    - Display ads: Images + Headlines + CTAs
    - RSY (Рекламная сеть Яндекса) banners
    """
    
    platform_name = "yandex"
    
    async def scan_and_analyze(self, landing_url: str) -> Dict[str, Any]:
        """Scan main page and discover relevant subpages."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Scan main page
            main_page = await self._scan_page(client, landing_url)
            
            # Discover relevant subpages
            subpages = await self._discover_subpages(client, landing_url, main_page)
            
            # Combine insights
            all_keywords = set(main_page.keywords)
            all_products = list(main_page.products)
            all_content = list(main_page.content_snippets)
            
            for page in subpages[:3]:  # Limit to 3 subpages
                all_keywords.update(page.keywords)
                all_products.extend(page.products)
                all_content.extend(page.content_snippets[:2])
            
            return {
                "platform": "yandex",
                "main_page": {
                    "title": main_page.title,
                    "description": main_page.description,
                },
                "keywords": list(all_keywords)[:20],
                "products": all_products[:10],
                "content_highlights": all_content[:10],
                "images": main_page.images[:5],
                "subpages_scanned": len(subpages),
            }
    
    async def _scan_page(self, client: httpx.AsyncClient, url: str) -> ScannedPage:
        """Scan a single page."""
        try:
            response = await client.get(url, follow_redirects=True)
            html = response.text
            
            # Use BeautifulSoup if available, otherwise regex
            if HAS_BS4:
                soup = BeautifulSoup(html, "html.parser")
                
                # Extract title
                title = soup.title.string if soup.title else ""
                
                # Extract meta description
                meta_desc = soup.find("meta", {"name": "description"})
                description = meta_desc.get("content", "") if meta_desc else ""
                
                # Extract meta keywords
                meta_keywords = soup.find("meta", {"name": "keywords"})
                keywords_raw = meta_keywords.get("content", "") if meta_keywords else ""
                keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
                
                # Extract headings
                headings = []
                for tag in ["h1", "h2", "h3"]:
                    for h in soup.find_all(tag):
                        text = h.get_text(strip=True)
                        if text and len(text) < 200:
                            headings.append(text)
                
                # Extract content snippets
                content_snippets = []
                for p in soup.find_all("p"):
                    text = p.get_text(strip=True)
                    if len(text) > 50 and len(text) < 500:
                        content_snippets.append(text)
                
                # Extract images
                images = []
                for img in soup.find_all("img"):
                    src = img.get("src", "")
                    if src and not src.startswith("data:"):
                        images.append(src)
                
                # Try to extract products (e-commerce)
                products = self._extract_products(soup)
            else:
                # Fallback: regex-based extraction
                title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
                title = title_match.group(1).strip() if title_match else ""
                
                desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.I)
                description = desc_match.group(1) if desc_match else ""
                
                kw_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\'](.*?)["\']', html, re.I)
                keywords_raw = kw_match.group(1) if kw_match else ""
                keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
                
                headings = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html, re.I | re.S)
                headings = [re.sub(r'<[^>]+>', '', h).strip()[:200] for h in headings if h.strip()]
                
                content_snippets = re.findall(r'<p[^>]*>(.*?)</p>', html, re.I | re.S)
                content_snippets = [
                    re.sub(r'<[^>]+>', '', p).strip()
                    for p in content_snippets
                    if 50 < len(re.sub(r'<[^>]+>', '', p).strip()) < 500
                ]
                
                images = re.findall(r'<img[^>]*src=["\']([^"\']+)["\']', html, re.I)
                images = [i for i in images if not i.startswith("data:")]
                
                products = []
            
            return ScannedPage(
                url=url,
                title=title,
                description=description,
                keywords=keywords,
                headings=headings[:10],
                content_snippets=content_snippets[:10],
                images=images[:10],
                products=products,
            )
        except Exception as e:
            return ScannedPage(
                url=url,
                title="",
                description="",
                keywords=[],
                headings=[],
                content_snippets=[],
                images=[],
                products=[],
            )
    
    async def _discover_subpages(
        self, client: httpx.AsyncClient, base_url: str, main_page: ScannedPage
    ) -> List[ScannedPage]:
        """Discover and scan relevant subpages."""
        # Priority pages to look for
        priority_paths = [
            "/catalog", "/products", "/services", "/about", 
            "/prices", "/contacts", "/delivery", "/pay"
        ]
        
        try:
            response = await client.get(base_url, follow_redirects=True)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find internal links
            found_urls = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                # Check if it's an internal link
                if href.startswith("/") and not href.startswith("//"):
                    for priority in priority_paths:
                        if priority in href.lower():
                            found_urls.add(base_url.rstrip("/") + href)
                            break
            
            # Scan found pages
            subpages = []
            for url in list(found_urls)[:5]:
                page = await self._scan_page(client, url)
                if page.title:  # Only add if successfully scanned
                    subpages.append(page)
            
            return subpages
        except:
            return []
    
    def _extract_products(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Try to extract product information."""
        products = []
        
        # Look for common product patterns
        product_selectors = [
            {"class": re.compile(r"product", re.I)},
            {"class": re.compile(r"item", re.I)},
            {"itemtype": "http://schema.org/Product"},
        ]
        
        for selector in product_selectors:
            for el in soup.find_all(attrs=selector)[:5]:
                name_el = el.find(["h2", "h3", "h4", "a"])
                price_el = el.find(class_=re.compile(r"price", re.I))
                
                if name_el:
                    products.append({
                        "name": name_el.get_text(strip=True)[:100],
                        "price": price_el.get_text(strip=True)[:50] if price_el else None,
                    })
        
        return products
    
    def build_generation_prompt(self, analysis: Dict[str, Any], description: str) -> str:
        """Build Yandex Direct specific prompt."""
        context = f"""
БИЗНЕС-КОНТЕКСТ:
- Заголовок сайта: {analysis.get('main_page', {}).get('title', 'N/A')}
- Описание: {analysis.get('main_page', {}).get('description', 'N/A')}
- Ключевые слова: {', '.join(analysis.get('keywords', [])[:10])}
- Проанализировано подстраниц: {analysis.get('subpages_scanned', 0)}
- Пользовательское описание: {description or 'не указано'}

ТОВАРЫ/УСЛУГИ:
{self._format_products(analysis.get('products', []))}

КОНТЕНТ-ХАЙЛАЙТЫ:
{chr(10).join(['- ' + c[:150] for c in analysis.get('content_highlights', [])[:5]])}
"""
        
        return f"""Ты — эксперт по контекстной рекламе в Яндекс Директ.

{context}

Создай 10 уникальных объявлений для Яндекс Директ.

ФОРМАТЫ:
1. Поисковые объявления (5 шт):
   - Заголовок 1: до 35 символов
   - Заголовок 2: до 30 символов
   - Текст: до 81 символа
   - Быстрые ссылки: 4 шт

2. РСЯ объявления (5 шт):
   - Заголовок: до 33 символов
   - Текст: до 75 символов
   - Призыв к действию

ТРЕБОВАНИЯ:
- Используй извлечённые ключевые слова
- Добавляй цены если найдены
- Пиши по-русски, живо и продающе
- Разные подходы: цена, качество, срочность, доверие, уникальность

Верни JSON:
{{
  "business_name": "название",
  "search_ads": [{{
    "title1": "...",
    "title2": "...", 
    "text": "...",
    "sitelinks": ["ссылка1", "ссылка2", "ссылка3", "ссылка4"],
    "approach": "подход"
  }}],
  "rsy_ads": [{{
    "title": "...",
    "text": "...",
    "cta": "призыв",
    "approach": "подход"
  }}]
}}
"""
    
    def _format_products(self, products: List[Dict[str, Any]]) -> str:
        """Format products for prompt."""
        if not products:
            return "Не найдены"
        return "\n".join([
            f"- {p['name']}" + (f" ({p['price']})" if p.get('price') else "")
            for p in products[:5]
        ])
    
    def get_ad_formats(self) -> List[str]:
        return ["search", "rsy", "smart_banners", "video"]


class OzonStrategy(PlatformStrategy):
    """
    Ozon Marketplace Strategy.
    
    Features:
    - Product card optimization
    - Marketplace-specific keywords
    - Rich content (A+ content style)
    - Brand store optimization
    """
    
    platform_name = "ozon"
    
    async def scan_and_analyze(self, landing_url: str) -> Dict[str, Any]:
        """Scan product or brand page on Ozon or external site."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(landing_url, follow_redirects=True)
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Check if it's Ozon product page
                is_ozon = "ozon.ru" in landing_url.lower()
                
                if is_ozon:
                    return await self._analyze_ozon_page(soup, landing_url)
                else:
                    return await self._analyze_external_for_ozon(soup, landing_url)
            except:
                return {"platform": "ozon", "error": True}
    
    async def _analyze_ozon_page(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Analyze Ozon product page."""
        # Extract product info from Ozon
        title = soup.find("h1")
        title_text = title.get_text(strip=True) if title else ""
        
        # Look for price
        price_el = soup.find(attrs={"data-widget": "webPrice"})
        price = price_el.get_text(strip=True) if price_el else None
        
        return {
            "platform": "ozon",
            "source": "ozon_product",
            "product_name": title_text,
            "price": price,
            "is_ozon_page": True,
        }
    
    async def _analyze_external_for_ozon(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Analyze external site for Ozon ad creation."""
        title = soup.title.string if soup.title else ""
        
        # Extract products
        products = []
        for el in soup.find_all(attrs={"class": re.compile(r"product", re.I)})[:10]:
            name = el.find(["h2", "h3", "a"])
            if name:
                products.append({"name": name.get_text(strip=True)[:100]})
        
        return {
            "platform": "ozon",
            "source": "external",
            "site_name": title,
            "products": products,
        }
    
    def build_generation_prompt(self, analysis: Dict[str, Any], description: str) -> str:
        """Build Ozon-specific prompt."""
        return f"""Ты — эксперт по продвижению на Ozon.

КОНТЕКСТ:
- Источник: {analysis.get('source', 'unknown')}
- Название: {analysis.get('product_name') or analysis.get('site_name', 'N/A')}
- Описание пользователя: {description or 'не указано'}

Создай контент для продвижения на Ozon:
1. 5 вариантов заголовков товарной карточки (до 200 символов)
2. 5 вариантов описаний (до 500 символов)
3. 10 ключевых слов для поиска на Ozon
4. 5 bullet points для характеристик

ТРЕБОВАНИЯ:
- Учитывай специфику маркетплейса
- SEO-оптимизация для поиска Ozon
- Продающий стиль

Верни JSON:
{{
  "titles": ["..."],
  "descriptions": ["..."],
  "keywords": ["..."],
  "bullet_points": ["..."]
}}
"""
    
    def get_ad_formats(self) -> List[str]:
        return ["product_card", "brand_store", "sponsored_products", "banners"]


class VKAdsStrategy(PlatformStrategy):
    """
    VK Ads Strategy.
    
    Features:
    - Social-first approach
    - Visual-heavy creatives
    - Stories, Reels, Feed formats
    - Community targeting
    """
    
    platform_name = "vk"
    
    async def scan_and_analyze(self, landing_url: str) -> Dict[str, Any]:
        """Scan page for VK ad creation."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(landing_url, follow_redirects=True)
                soup = BeautifulSoup(response.text, "html.parser")
                
                title = soup.title.string if soup.title else ""
                
                # Extract images for visual-heavy VK ads
                images = []
                for img in soup.find_all("img"):
                    src = img.get("src", "")
                    if src and not src.startswith("data:") and "logo" not in src.lower():
                        images.append(src)
                
                # Extract social proof
                reviews = soup.find_all(attrs={"class": re.compile(r"review|testimonial", re.I)})
                
                return {
                    "platform": "vk",
                    "title": title,
                    "images": images[:10],
                    "has_reviews": len(reviews) > 0,
                }
            except:
                return {"platform": "vk", "error": True}
    
    def build_generation_prompt(self, analysis: Dict[str, Any], description: str) -> str:
        """Build VK Ads specific prompt."""
        return f"""Ты — эксперт по рекламе VK.

КОНТЕКСТ:
- Название: {analysis.get('title', 'N/A')}
- Найдено изображений: {len(analysis.get('images', []))}
- Есть отзывы: {'да' if analysis.get('has_reviews') else 'нет'}
- Описание: {description or 'не указано'}

Создай 10 креативов для VK Ads:

ФОРМАТЫ:
1. Универсальные записи (5 шт):
   - Заголовок: до 33 символов
   - Текст: до 220 символов
   - Призыв к действию

2. Истории/Клипы (5 шт):
   - Короткий текст: до 50 символов
   - Призыв: 1-2 слова
   - Описание визуала

ТРЕБОВАНИЯ:
- Живой, разговорный стиль
- Эмодзи где уместно
- Акцент на визуал
- Разные подходы: FOMO, социальное доказательство, выгода

Верни JSON:
{{
  "posts": [{{
    "title": "...",
    "text": "...",
    "cta": "...",
    "approach": "..."
  }}],
  "stories": [{{
    "text": "...",
    "cta": "...",
    "visual_description": "...",
    "approach": "..."
  }}]
}}
"""
    
    def get_ad_formats(self) -> List[str]:
        return ["feed_post", "stories", "clips", "carousel", "lead_forms"]


# Registry of platform strategies
PLATFORM_STRATEGIES: Dict[str, PlatformStrategy] = {
    "yandex": YandexDirectStrategy(),
    "ozon": OzonStrategy(),
    "vk": VKAdsStrategy(),
}


def get_strategy(platform: str) -> PlatformStrategy:
    """Get strategy for platform."""
    return PLATFORM_STRATEGIES.get(platform, YandexDirectStrategy())
