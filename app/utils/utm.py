from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse
from typing import Optional
from app.db.models import Platform, OrgUtmSettings

def build_utm_url(base_url: str, utm: dict) -> str:
    """
    Builds a final URL by appending UTM parameters to the base URL.
    Preserves existing query parameters and fragments.
    Filters out empty UTM values.
    Sorts UTM parameters for deterministic output.
    """
    if not base_url:
        return ""

    parsed = urlparse(base_url)
    existing_query = parse_qsl(parsed.query)

    # Filter empty values and sort keys
    utm_params = sorted(
        [(k, v) for k, v in utm.items() if v is not None and str(v).strip() != ""],
        key=lambda x: x[0]
    )

    # Combine existing query with new UTM params
    # Note: UTMs are appended. If a key exists in both, both are kept (standard behavior),
    # or we could override. Usually UTMs shouldn't be in base_url, so appending is safe.
    final_query = existing_query + utm_params

    encoded_query = urlencode(final_query)

    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        encoded_query,
        parsed.fragment
    ))


def build_utm_from_org_settings(
    base_url: str,
    org_settings: Optional[OrgUtmSettings],
    platform: Platform,
    campaign_id: Optional[str] = None,
    ad_group_id: Optional[str] = None,
    ad_id: Optional[str] = None,
    custom_utm: Optional[dict] = None
) -> str:
    """
    Builds final URL using organization UTM settings templates.
    Merges with custom_utm if provided (custom takes precedence).
    
    Args:
        base_url: Base URL to append UTM to
        org_settings: Organization UTM settings (can be None for defaults)
        platform: Platform enum
        campaign_id: Campaign external ID for template replacement
        ad_group_id: Ad group external ID for template replacement
        ad_id: Ad external ID for template replacement
        custom_utm: Optional custom UTM parameters (merged with org settings)
    """
    if not base_url:
        return ""
    
    # Get templates from org settings or use defaults
    s_source = org_settings.utm_source if org_settings else "{platform}"
    s_medium = org_settings.utm_medium if org_settings else "cpc"
    s_campaign = org_settings.utm_campaign_tpl if org_settings else "{campaign_id}"
    s_content = org_settings.utm_content_tpl if org_settings else "{ad_id}"
    s_term = org_settings.utm_term_tpl if org_settings else None
    
    # Replace placeholders in templates
    def replace_template(tpl: Optional[str]) -> Optional[str]:
        if not tpl:
            return None
        res = tpl.replace("{platform}", platform.value)
        res = res.replace("{campaign_id}", campaign_id or "")
        res = res.replace("{ad_group_id}", ad_group_id or "")
        res = res.replace("{ad_id}", ad_id or "")
        return res if res else None
    
    # Build UTM params from templates
    utm_params = {
        "utm_source": replace_template(s_source),
        "utm_medium": replace_template(s_medium),
        "utm_campaign": replace_template(s_campaign),
        "utm_content": replace_template(s_content),
        "utm_term": replace_template(s_term),
    }
    
    # Filter empty values
    utm_params = {k: v for k, v in utm_params.items() if v}
    
    # Merge with custom UTM (custom takes precedence)
    if custom_utm:
        utm_params.update({k: v for k, v in custom_utm.items() if v})
    
    # Build final URL
    return build_utm_url(base_url, utm_params)
