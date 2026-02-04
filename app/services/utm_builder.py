"""
UTM Builder Service.

Professional UTM parameter generator for campaign tracking.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
import uuid


@dataclass
class UTMParams:
    """UTM parameters."""
    utm_source: str
    utm_medium: str
    utm_campaign: str
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None


class UTMBuilder:
    """
    Professional UTM parameter builder.
    
    Supports platform-specific templates and batch generation.
    """
    
    PLATFORM_TEMPLATES = {
        "yandex": {
            "utm_source": "yandex",
            "utm_medium": "cpc",
            "utm_campaign": "{campaign_name}",
            "utm_term": "{keyword}",
            "utm_content": "{ad_id}",
        },
        "vk": {
            "utm_source": "vk",
            "utm_medium": "social",
            "utm_campaign": "{campaign_name}",
            "utm_content": "{ad_id}",
        },
        "ozon": {
            "utm_source": "ozon",
            "utm_medium": "marketplace",
            "utm_campaign": "{campaign_name}",
            "utm_content": "{product_id}",
        },
        "google": {
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": "{campaign_name}",
            "utm_term": "{keyword}",
            "utm_content": "{ad_id}",
        },
    }
    
    @classmethod
    def build_url(
        cls,
        base_url: str,
        utm_source: str,
        utm_medium: str,
        utm_campaign: str,
        utm_term: Optional[str] = None,
        utm_content: Optional[str] = None,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build URL with UTM parameters."""
        parsed = urlparse(base_url)
        
        # Existing query params
        existing = parse_qs(parsed.query)
        
        # UTM params
        params = {
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": utm_campaign,
        }
        
        if utm_term:
            params["utm_term"] = utm_term
        if utm_content:
            params["utm_content"] = utm_content
        if extra_params:
            params.update(extra_params)
        
        # Merge with existing (UTM overrides)
        for key, value in existing.items():
            if key not in params:
                params[key] = value[0] if len(value) == 1 else value
        
        # Build new URL
        new_query = urlencode(params)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        ))
        
        return new_url
    
    @classmethod
    def from_platform(
        cls,
        base_url: str,
        platform: str,
        campaign_name: str,
        ad_id: Optional[str] = None,
        keyword: Optional[str] = None,
        product_id: Optional[str] = None,
    ) -> str:
        """Build URL using platform template."""
        template = cls.PLATFORM_TEMPLATES.get(platform, cls.PLATFORM_TEMPLATES["yandex"])
        
        # Fill template
        params = {}
        for key, value in template.items():
            filled = value.format(
                campaign_name=campaign_name,
                ad_id=ad_id or "",
                keyword=keyword or "",
                product_id=product_id or "",
            )
            if filled:
                params[key] = filled
        
        return cls.build_url(base_url, **params)
    
    @classmethod
    def batch_generate(
        cls,
        base_url: str,
        utm_source: str,
        utm_medium: str,
        campaign_name: str,
        variations: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """
        Generate multiple URLs with different UTM content.
        
        Args:
            variations: List of {"name": "...", "utm_content": "...", ...}
        """
        results = []
        
        for i, var in enumerate(variations):
            url = cls.build_url(
                base_url=base_url,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=campaign_name,
                utm_content=var.get("utm_content", f"var{i+1}"),
                utm_term=var.get("utm_term"),
            )
            
            results.append({
                "name": var.get("name", f"Вариант {i+1}"),
                "url": url,
                "utm_content": var.get("utm_content", f"var{i+1}"),
            })
        
        return results
    
    @classmethod
    def generate_tracking_id(cls) -> str:
        """Generate unique tracking ID for custom attribution."""
        return f"rek_{uuid.uuid4().hex[:12]}"
    
    @classmethod
    def add_reklai_tracking(cls, url: str, organization_id: int, campaign_id: int) -> str:
        """Add Reklai-specific tracking parameters."""
        tracking_id = cls.generate_tracking_id()
        
        return cls.build_url(
            url,
            utm_source="reklai",
            utm_medium="platform",
            utm_campaign=str(campaign_id),
            extra_params={
                "rek_org": str(organization_id),
                "rek_cid": str(campaign_id),
                "rek_tid": tracking_id,
            },
        )
