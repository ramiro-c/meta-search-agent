from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from meta_search.dedup import deduplicate_results
from meta_search.filter import cheap_filter
from meta_search.fusion import reciprocal_rank_fusion
from meta_search.judge import llm_judge
from meta_search.models import FusedResult, SearchResponse, SearchResult
from meta_search.normalize import normalize_result
from meta_search.providers import get_enabled_providers
from meta_search.providers.base import SearchProvider
from meta_search.rewrite import expand_query_variants

logger = logging.getLogger(__name__)


async def run_meta_search(
    query: str,
    *,
    providers_only: list[str] | None = None,
    timeout: float | None = None,
    max_results_per_provider: int = 10,
    max_output: int = 20,
    use_llm_rewrite: bool = False,
    use_llm_judge: bool = True,
    skip_cheap_filter: bool = False,
) -> SearchResponse:
    variants = await expand_query_variants(query, use_llm=use_llm_rewrite)
    providers = get_enabled_providers(
        timeout=timeout,
        max_results=max_results_per_provider,
        only=providers_only,
    )
    if not providers:
        return SearchResponse(
            query=query,
            query_variants=variants,
            providers_used=[],
            results=[],
        )

    provider_lists: dict[str, list[SearchResult]] = defaultdict(list)
    failed: list[str] = []

    async def run_one(provider: SearchProvider, variant: str) -> None:
        try:
            hits = await asyncio.wait_for(
                provider.search(variant, query_variant=variant),
                timeout=provider._timeout,
            )
            normalized = [normalize_result(h) for h in hits if h.url]
            provider_lists[provider.name].extend(normalized)
        except Exception as exc:
            logger.warning("Provider %s failed for '%s': %s", provider.name, variant, exc)
            if provider.name not in failed:
                failed.append(provider.name)

    tasks = [
        run_one(p, v) for p in providers for v in variants
    ]
    await asyncio.gather(*tasks)

    # Dedup within each provider list (same URL from multiple variants)
    for name in list(provider_lists.keys()):
        provider_lists[name] = deduplicate_results(provider_lists[name])

    raw_count = sum(len(v) for v in provider_lists.values())
    fused = reciprocal_rank_fusion(dict(provider_lists))

    if not skip_cheap_filter:
        fused = cheap_filter(fused, query, max_results=max_output * 2)

    if use_llm_judge:
        fused = await llm_judge(query, fused, top_k=max_output)

    fused = fused[:max_output]

    return SearchResponse(
        query=query,
        query_variants=variants,
        providers_used=[p.name for p in providers],
        providers_failed=failed,
        results=fused,
        raw_count=raw_count,
        fused_count=len(fused),
    )
