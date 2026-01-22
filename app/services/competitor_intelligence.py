"""
Competitor Intelligence Service.

AI-powered competitor analysis:
- Discover competitor domains
- Analyze their ads (where accessible)
- Identify gaps and opportunities
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import httpx
import re
import logging

# Optional BeautifulSoup import
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None

from app.core.ai.openai_provider import get_text_provider

logger = logging.getLogger(__name__)


@dataclass
class CompetitorProfile:
    """Competitor business profile."""
    domain: str
    name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    products: List[str] = None
    unique_selling_points: List[str] = None
    pricing_info: Optional[str] = None
    trust_signals: List[str] = None
    social_links: List[str] = None


@dataclass
class CompetitorAd:
    """Discovered competitor ad."""
    platform: str
    headline: Optional[str] = None
    description: Optional[str] = None
    display_url: Optional[str] = None
    call_to_action: Optional[str] = None
    creative_url: Optional[str] = None


@dataclass
class CompetitorAnalysis:
    """Full competitor analysis result."""
    domain: str
    profile: CompetitorProfile
    ads: List[CompetitorAd]
    keywords: List[str]
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    recommendations: List[str]
    analyzed_at: datetime


class CompetitorIntelligence:
    """
    AI-powered competitor analysis service.
    """
    
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    
    async def analyze_competitor(self, domain: str) -> CompetitorAnalysis:
        """
        Perform full competitor analysis.
        
        Args:
            domain: Competitor domain to analyze
        """
        # Normalize domain
        domain = domain.lower().strip()
        if domain.startswith("http"):
            domain = domain.split("//")[1].split("/")[0]
        
        # Scan their website
        profile = await self._scan_website(f"https://{domain}")
        
        # Discover keywords they target
        keywords = await self._extract_seo_keywords(f"https://{domain}")
        
        # Analyze with AI
        ai_analysis = await self._ai_analyze(profile, keywords)
        
        return CompetitorAnalysis(
            domain=domain,
            profile=profile,
            ads=[],  # Would need ad library access
            keywords=keywords,
            strengths=ai_analysis.get("strengths", []),
            weaknesses=ai_analysis.get("weaknesses", []),
            opportunities=ai_analysis.get("opportunities", []),
            recommendations=ai_analysis.get("recommendations", []),
            analyzed_at=datetime.utcnow(),
        )
    
    async def find_competitors(self, my_domain: str, industry: str) -> List[str]:
        """
        Find potential competitors based on industry and domain.
        """
        # Use AI to suggest competitors
        provider = get_text_provider()
        
        prompt = f"""
На основе домена {my_domain} и отрасли "{industry}", 
предложи 5-10 основных конкурентов в России.

Верни JSON:
{{"competitors": ["domain1.ru", "domain2.com", ...]}}
"""
        
        try:
            response = await provider.generate_text(
                prompt=prompt,
                json_schema={"type": "object", "properties": {"competitors": {"type": "array"}}}
            )
            import json
            data = json.loads(response)
            return data.get("competitors", [])
        except Exception as e:
            logger.exception(f"Error finding competitors: {e}")
            return []
    
    async def _scan_website(self, url: str) -> CompetitorProfile:
        """Scan competitor website for business info."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        try:
            response = await self._client.get(url)
            html = response.text
            
            if HAS_BS4:
                soup = BeautifulSoup(html, "html.parser")
                
                # Extract basic info
                title = soup.title.string if soup.title else ""
                
                meta_desc = soup.find("meta", {"name": "description"})
                description = meta_desc.get("content", "") if meta_desc else ""
                
                # Extract products/services
                products = []
                for el in soup.find_all(["h2", "h3"], limit=20):
                    text = el.get_text(strip=True)
                    if len(text) < 100 and len(text) > 3:
                        products.append(text)
                
                # Find trust signals
                trust_signals = []
                trust_keywords = ["лет на рынке", "клиентов", "гарантия", "сертификат", "лицензия"]
                for p in soup.find_all("p"):
                    text = p.get_text(strip=True).lower()
                    for kw in trust_keywords:
                        if kw in text:
                            trust_signals.append(p.get_text(strip=True)[:200])
                            break
                
                social_links = []
                social_hosts = ("vk.com", "t.me", "instagram.com", "facebook.com", "ok.ru", "youtube.com")
                for a in soup.find_all("a", href=True):
                    href = a.get("href", "").strip()
                    if any(host in href for host in social_hosts):
                        social_links.append(href)
                social_links = list(dict.fromkeys(social_links))  # keep order, unique
            else:
                # Fallback: regex
                title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
                title = title_match.group(1).strip() if title_match else ""
                
                desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.I)
                description = desc_match.group(1) if desc_match else ""
                
                headings = re.findall(r'<h[2-3][^>]*>(.*?)</h[2-3]>', html, re.I | re.S)
                products = [re.sub(r'<[^>]+>', '', h).strip()[:100] for h in headings if 3 < len(re.sub(r'<[^>]+>', '', h).strip()) < 100]
                
                trust_signals = []
                social_links = []
            
            # Find company name
            name = title.split("|")[0].split("-")[0].strip() if title else None
            
            return CompetitorProfile(
                domain=domain,
                name=name,
                description=description[:500] if description else None,
                products=products[:10],
                trust_signals=trust_signals[:5] if HAS_BS4 else [],
                social_links=social_links[:5] if HAS_BS4 else [],
            )
        except Exception as e:
            logger.exception(f"Error scanning {url}: {e}")
            return CompetitorProfile(domain=domain)
    
    async def _extract_seo_keywords(self, url: str) -> List[str]:
        """Extract SEO keywords from competitor site."""
        try:
            response = await self._client.get(url)
            html = response.text
            keywords = set()
            
            if HAS_BS4:
                soup = BeautifulSoup(html, "html.parser")
                
                # Meta keywords
                meta_kw = soup.find("meta", {"name": "keywords"})
                if meta_kw:
                    for kw in meta_kw.get("content", "").split(","):
                        kw = kw.strip()
                        if kw:
                            keywords.add(kw)
                
                # H1-H3 headings
                for tag in ["h1", "h2", "h3"]:
                    for el in soup.find_all(tag):
                        text = el.get_text(strip=True)
                        if len(text) < 50:
                            keywords.add(text)
                
                # Title words
                if soup.title and soup.title.string:
                    for word in soup.title.string.split():
                        if len(word) > 3:
                            keywords.add(word)
            else:
                # Fallback: regex
                kw_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\'](.*?)["\']', html, re.I)
                if kw_match:
                    for kw in kw_match.group(1).split(","):
                        kw = kw.strip()
                        if kw:
                            keywords.add(kw)
                
                headings = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html, re.I | re.S)
                for h in headings:
                    text = re.sub(r'<[^>]+>', '', h).strip()
                    if len(text) < 50:
                        keywords.add(text)
                
                title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
                if title_match:
                    for word in title_match.group(1).split():
                        if len(word) > 3:
                            keywords.add(word)
            
            return list(keywords)[:30]
        except Exception as e:
            logger.exception(f"Error extracting keywords: {e}")
            return []
    
    async def _ai_analyze(
        self,
        profile: CompetitorProfile,
        keywords: List[str],
    ) -> Dict[str, List[str]]:
        """Use AI to analyze competitor and find opportunities."""
        provider = get_text_provider()
        
        profile_text = f"""
Домен: {profile.domain}
Название: {profile.name}
Описание: {profile.description}
Продукты: {', '.join(profile.products or [])}
Доверительные сигналы: {', '.join(profile.trust_signals or [])}
Ключевые слова: {', '.join(keywords[:15])}
"""
        
        prompt = f"""
Проанализируй конкурента:

{profile_text}

Верни JSON:
{{
  "strengths": ["их сильные стороны..."],
  "weaknesses": ["их слабые стороны/пробелы..."],
  "opportunities": ["возможности для нас..."],
  "recommendations": ["конкретные рекомендации для рекламы..."]
}}

По каждому пункту дай 3-5 конкретных insights.
"""
        
        try:
            response = await provider.generate_text(
                prompt=prompt,
                json_schema={
                    "type": "object",
                    "properties": {
                        "strengths": {"type": "array", "items": {"type": "string"}},
                        "weaknesses": {"type": "array", "items": {"type": "string"}},
                        "opportunities": {"type": "array", "items": {"type": "string"}},
                        "recommendations": {"type": "array", "items": {"type": "string"}},
                    },
                },
            )
            if isinstance(response, dict):
                return self._normalize_analysis(response, profile, keywords)
            return self._normalize_analysis({}, profile, keywords)
        except Exception as e:
            logger.exception(f"Error in AI analysis: {e}")
            return self._normalize_analysis({}, profile, keywords)

    @staticmethod
    def _normalize_analysis(
        data: Dict[str, Any],
        profile: CompetitorProfile,
        keywords: List[str],
    ) -> Dict[str, List[str]]:
        def _as_list(value: Any) -> List[str]:
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            return []

        strengths = _as_list(data.get("strengths"))
        weaknesses = _as_list(data.get("weaknesses"))
        opportunities = _as_list(data.get("opportunities"))
        recommendations = _as_list(data.get("recommendations"))

        if not strengths:
            strengths = (profile.trust_signals or [])[:3] or (profile.products or [])[:3]
        if not weaknesses:
            weaknesses = []
            if not profile.description:
                weaknesses.append("На сайте не найдено подробного описания.")
            if not profile.products:
                weaknesses.append("Не удалось выделить список продуктов/услуг.")
            if not profile.social_links:
                weaknesses.append("Не найдено публичных ссылок на соцсети.")
        if not opportunities:
            opportunities = [f"Усилить ключевой запрос: {kw}" for kw in (keywords or [])[:3]]
        if not recommendations:
            recommendations = (profile.products or keywords or [])[:5]
            recommendations = [f"Подсветить «{item}» в рекламе" for item in recommendations]

        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "recommendations": recommendations,
        }
    
    async def compare_with_competitor(
        self,
        my_domain: str,
        competitor_domain: str,
    ) -> Dict[str, Any]:
        """Compare your business with a competitor."""
        my_profile = await self._scan_website(f"https://{my_domain}")
        competitor_profile = await self._scan_website(f"https://{competitor_domain}")
        
        provider = get_text_provider()
        
        prompt = f"""
Сравни два бизнеса:

МЫ ({my_domain}):
- {my_profile.description}
- Продукты: {', '.join(my_profile.products or [])}

КОНКУРЕНТ ({competitor_domain}):
- {competitor_profile.description}
- Продукты: {', '.join(competitor_profile.products or [])}

Выдай JSON:
{{
  "our_advantages": ["наши преимущества..."],
  "competitor_advantages": ["их преимущества..."],
  "differentiation_ideas": ["как отстроиться..."],
  "ad_angles": ["углы для рекламы против них..."]
}}
"""
        
        try:
            response = await provider.generate_text(prompt=prompt)
            import json
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            logger.exception(f"Error comparing: {e}")
            return {}
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
