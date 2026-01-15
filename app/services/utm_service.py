from __future__ import annotations

import hashlib
from typing import Any
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

from app.db.models import OrgUtmSettings, OrgUtmRule, Platform


_ALLOWED_SCHEMES = {"http", "https"}
_UTM_KEYS = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"}


def normalize_and_validate_url(url: str | None) -> tuple[bool, str | None, str | None]:
    if not url:
        return False, "missing_url", None
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return False, "blocked_scheme", None
    if not parsed.netloc:
        return False, "invalid_url", None
    normalized = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )
    return True, None, normalized


def compute_utm_hash(final_url: str) -> str:
    return hashlib.sha256(final_url.encode("utf-8")).hexdigest()


def _replace_template(tpl: str | None, context: dict[str, Any]) -> str | None:
    if not tpl:
        return None
    res = tpl
    for key, value in context.items():
        res = res.replace(f"{{{key}}}", str(value or ""))
    return res if res else None


def _build_from_settings(org_settings: OrgUtmSettings | None, context: dict[str, Any]) -> dict[str, str]:
    s_source = org_settings.utm_source if org_settings else "{platform}"
    s_medium = org_settings.utm_medium if org_settings else "cpc"
    s_campaign = org_settings.utm_campaign_tpl if org_settings else "{campaign_id}"
    s_content = org_settings.utm_content_tpl if org_settings else "{ad_id}"
    s_term = org_settings.utm_term_tpl if org_settings else None

    params = {
        "utm_source": _replace_template(s_source, context),
        "utm_medium": _replace_template(s_medium, context),
        "utm_campaign": _replace_template(s_campaign, context),
        "utm_content": _replace_template(s_content, context),
        "utm_term": _replace_template(s_term, context),
    }
    return {k: v for k, v in params.items() if v}


def _apply_rule_override(rule: OrgUtmRule | None, context: dict[str, Any]) -> dict[str, str]:
    if not rule or not rule.template_json:
        return {}

    params: dict[str, str | None] = {}
    for key, value in rule.template_json.items():
        if key.endswith("_tpl"):
            params[key.replace("_tpl", "")] = _replace_template(str(value), context) if value else None
        elif key in _UTM_KEYS:
            params[key] = str(value) if value is not None else None
    return {k: v for k, v in params.items() if v}


def build_utm_params(
    org_settings: OrgUtmSettings | None,
    rule_override: OrgUtmRule | None,
    *,
    platform: Platform | None,
    campaign_id: str | None,
    ad_group_id: str | None,
    ad_id: str | None,
) -> dict[str, str]:
    context = {
        "platform": platform.value if platform else "",
        "campaign_id": campaign_id or "",
        "ad_group_id": ad_group_id or "",
        "ad_id": ad_id or "",
    }
    params = _build_from_settings(org_settings, context)
    params.update(_apply_rule_override(rule_override, context))
    return params


def apply_utm(url: str, params: dict[str, str]) -> str:
    parsed = urlparse(url)
    existing_query = parse_qsl(parsed.query)
    existing_query = [(k, v) for k, v in existing_query if k not in _UTM_KEYS]
    utm_items = sorted([(k, v) for k, v in params.items() if v], key=lambda x: x[0])
    final_query = existing_query + utm_items
    encoded_query = urlencode(final_query)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, encoded_query, parsed.fragment)
    )


def pick_matching_rule(rules: list[OrgUtmRule], *, platform: Platform | None, connection_id: int, campaign_name: str | None, ad_group_name: str | None, ad_name: str | None) -> OrgUtmRule | None:
    def _contains(hay: str | None, needle: str | None) -> bool:
        if not needle:
            return True
        if not hay:
            return False
        return needle.lower() in hay.lower()

    for rule in rules:
        if not rule.is_enabled:
            continue
        if rule.match_platform and (not platform or rule.match_platform != platform):
            continue
        if rule.match_connection_id and rule.match_connection_id != connection_id:
            continue
        if not _contains(campaign_name, rule.match_campaign_contains):
            continue
        if not _contains(ad_group_name, rule.match_ad_group_contains):
            continue
        if not _contains(ad_name, rule.match_ad_contains):
            continue
        return rule
    return None
