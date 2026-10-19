from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from meta_search.models import SearchResult

_TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "ref",
        "ref_src",
    }
)


def canonicalize_url(url: str) -> str:
    """Normalize URL for deduplication (lowercase host, strip tracking, trailing slash)."""
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    scheme = (parsed.scheme or "https").lower()
    netloc = (parsed.netloc or "").lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    query_pairs = parse_qs(parsed.query, keep_blank_values=False)
    filtered = [
        (k, v[0])
        for k, v in sorted(query_pairs.items())
        if k.lower() not in _TRACKING_PARAMS and v
    ]
    query = urlencode(filtered) if filtered else ""
    return urlunparse((scheme, netloc, path, "", query, ""))


def normalize_result(result: SearchResult) -> SearchResult:
    """Apply URL canonicalization and light text cleanup."""
    canon = canonicalize_url(result.url)
    title = _clean_text(result.title)
    snippet = _clean_text(result.snippet)
    return result.model_copy(
        update={"url": canon or result.url, "title": title, "snippet": snippet}
    )


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text.strip())
    return text
