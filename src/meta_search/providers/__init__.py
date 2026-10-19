from __future__ import annotations

from meta_search.providers.base import SearchProvider
from meta_search.providers.brave import BraveProvider
from meta_search.providers.duckduckgo import DuckDuckGoProvider
from meta_search.providers.exa import ExaProvider
from meta_search.providers.tavily import TavilyProvider
from meta_search.providers.wikipedia import WikipediaProvider

ALL_PROVIDER_CLASSES: list[type[SearchProvider]] = [
    BraveProvider,
    ExaProvider,
    TavilyProvider,
    DuckDuckGoProvider,
    WikipediaProvider,
]


def get_enabled_providers(
    timeout: float | None = None,
    max_results: int | None = None,
    only: list[str] | None = None,
) -> list[SearchProvider]:
    providers: list[SearchProvider] = []
    for cls in ALL_PROVIDER_CLASSES:
        if only and cls.config.name not in only:
            continue
        if cls.is_enabled():
            providers.append(cls(timeout=timeout, max_results=max_results))
    return providers
