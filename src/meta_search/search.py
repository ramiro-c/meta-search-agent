from __future__ import annotations

from typing import Any

from meta_search.models import SearchResponse
from meta_search.orchestrator import run_meta_search


async def search(
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
    """Library entrypoint for agents."""
    return await run_meta_search(
        query,
        providers_only=providers_only,
        timeout=timeout,
        max_results_per_provider=max_results_per_provider,
        max_output=max_output,
        use_llm_rewrite=use_llm_rewrite,
        use_llm_judge=use_llm_judge,
        skip_cheap_filter=skip_cheap_filter,
    )


async def search_json(
    query: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Return search results as a JSON-serializable dict."""
    resp = await search(query, **kwargs)
    return resp.model_dump_json_ready()
