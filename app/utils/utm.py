from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

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
