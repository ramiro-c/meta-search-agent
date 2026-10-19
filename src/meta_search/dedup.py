from __future__ import annotations

from meta_search.models import SearchResult


def deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    """
    Collapse hits with the same canonical URL, keeping the best rank per provider
    and merging metadata from duplicates.
    """
    by_url: dict[str, SearchResult] = {}
    for r in results:
        if not r.url:
            continue
        existing = by_url.get(r.url)
        if existing is None:
            by_url[r.url] = r
            continue
        if r.rank < existing.rank:
            by_url[r.url] = r.model_copy(
                update={
                    "title": r.title or existing.title,
                    "snippet": r.snippet or existing.snippet,
                    "published": r.published or existing.published,
                }
            )
        else:
            by_url[r.url] = existing.model_copy(
                update={
                    "title": existing.title or r.title,
                    "snippet": existing.snippet or r.snippet,
                    "published": existing.published or r.published,
                }
            )
    return list(by_url.values())
