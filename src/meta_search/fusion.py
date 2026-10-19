from __future__ import annotations

from collections import defaultdict

from meta_search.models import FusedResult, SearchResult

RRF_K = 60


def reciprocal_rank_fusion(
    provider_lists: dict[str, list[SearchResult]],
    k: int = RRF_K,
) -> list[FusedResult]:
    """
    Fuse ranked lists with Reciprocal Rank Fusion.
    Tracks which providers contributed each URL and their ranks.
    """
    scores: dict[str, float] = defaultdict(float)
    meta: dict[str, SearchResult] = {}
    providers_by_url: dict[str, set[str]] = defaultdict(set)
    ranks_by_url: dict[str, dict[str, int]] = defaultdict(dict)

    for provider, hits in provider_lists.items():
        for hit in hits:
            if not hit.url:
                continue
            scores[hit.url] += 1.0 / (k + hit.rank)
            providers_by_url[hit.url].add(provider)
            ranks_by_url[hit.url][provider] = hit.rank
            if hit.url not in meta or hit.rank < meta[hit.url].rank:
                meta[hit.url] = hit

    sorted_urls = sorted(scores.keys(), key=lambda u: scores[u], reverse=True)
    fused: list[FusedResult] = []
    for url in sorted_urls:
        base = meta[url]
        fused.append(
            FusedResult(
                url=url,
                title=base.title,
                snippet=base.snippet,
                published=base.published,
                providers=sorted(providers_by_url[url]),
                provider_ranks=dict(ranks_by_url[url]),
                rrf_score=scores[url],
            )
        )
    return fused
