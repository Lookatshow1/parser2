import logging
import httpx
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models_context import BusinessContext

logger = logging.getLogger(__name__)

class WebsiteParserService:
    def __init__(self, db: Session):
        self.db = db

    async def parse_and_save(self, url: str, org_id: int) -> BusinessContext:
        """
        Parses a website and saves the context to DB.
        """
        # Check existing (optional, for now always create new or update latest)
        
        ctx = BusinessContext(
            organization_id=org_id,
            url=url,
            domain=urlparse(url).netloc,
            status="parsing"
        )
        self.db.add(ctx)
        self.db.commit()
        self.db.refresh(ctx)

        try:
            cleaned_text, meta = await self._scrape_content(url)
            
            ctx.clean_text = cleaned_text
            ctx.meta_title = meta.get("title")
            ctx.meta_description = meta.get("description")
            ctx.status = "success"
            
        except Exception as e:
            logger.error(f"Failed to parse {url}: {e}")
            ctx.status = "failed"
            ctx.error = str(e)
        
        ctx.updated_at = datetime.utcnow()
        self.db.commit()
        return ctx

    async def parse_only(self, url: str) -> str:
        """
        Parses a website and returns text without saving to DB.
        """
        try:
            text, _ = await self._scrape_content(url)
            return text
        except Exception as e:
             logger.error(f"Failed to parse {url}: {e}")
             return ""

    async def _scrape_content(self, url: str) -> tuple[str, dict]:
        """
        Scrapes content using httpx and BeautifulSoup.
        Returns (clean_text, meta_dict).
        """
        if not url.startswith("http"):
            url = f"https://{url}"

        headers = {"User-Agent": "Mozilla/5.0 (compatible; Business-Context-Bot/1.0)"}
        
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract Meta
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        desc_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        description = desc_tag.get('content', '').strip() if desc_tag else ""
        
        meta = {"title": title, "description": description}

        # Cleanup
        for script in soup(["script", "style", "nav", "footer", "iframe", "noscript", "header"]):
            script.extract()

        # Extract Text
        text_blocks = []
        # Priority tags
        for tag in ['h1', 'h2', 'h3', 'p', 'li', 'article', 'section']:
            for el in soup.find_all(tag):
                text = el.get_text(strip=True)
                if text and len(text) > 20: 
                    text_blocks.append(text)
        
        # Deduplicate and Join
        seen = set()
        unique_blocks = []
        for b in text_blocks:
            if b not in seen:
                seen.add(b)
                unique_blocks.append(b)
        
        # Limit length
        full_text = "\n\n".join(unique_blocks[:50])
        return full_text[:10000], meta

    def get_context(self, context_id: int) -> BusinessContext | None:
        return self.db.get(BusinessContext, context_id)
