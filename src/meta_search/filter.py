from __future__ import annotations

import re

from meta_search.models import FusedResult

_BLOCKED_HOST_SUFFIXES = (
    "pinterest.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
)


def cheap_filter(
    results: list[FusedResult],
    query: str,
    *,
    min_snippet_len: int = 20,
    max_results: int | None = None,
) -> list[FusedResult]:
    """
    Fast heuristic filter: drop empty/low-signal hits and obvious junk hosts.
    """
    tokens = _query_tokens(query)
    scored: list[tuple[float, FusedResult]] = []
    for r in results:
        if not r.url or not r.title:
            continue
        host = _host(r.url)
        if any(host.endswith(s) for s in _BLOCKED_HOST_SUFFIXES):
            continue
        if len(r.snippet or "") < min_snippet_len and len(r.title) < 10:
            continue
        overlap = _token_overlap(tokens, r.title + " " + r.snippet)
        scored.append((overlap + r.rrf_score * 0.01, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    filtered = [r for _, r in scored]
    if max_results is not None:
        filtered = filtered[:max_results]
    return filtered


def _query_tokens(query: str) -> set[str]:
    return {t.lower() for t in re.findall(r"\w+", query) if len(t) > 2}


def _token_overlap(tokens: set[str], text: str) -> float:
    if not tokens:
        return 0.0
    words = set(re.findall(r"\w+", text.lower()))
    return len(tokens & words) / len(tokens)


def _host(url: str) -> str:
    from urllib.parse import urlparse

    return (urlparse(url).netloc or "").lower().lstrip("www.")
