from __future__ import annotations

import abc
import os
from dataclasses import dataclass

from meta_search.models import SearchResult


@dataclass
class ProviderConfig:
    name: str
    api_key_env: str | None
    default_timeout: float = 15.0
    max_results: int = 10


class SearchProvider(abc.ABC):
    """Pluggable adapter for a web search / indexer API."""

    config: ProviderConfig

    def __init__(self, timeout: float | None = None, max_results: int | None = None):
        self._timeout = timeout if timeout is not None else self.config.default_timeout
        self._max_results = max_results if max_results is not None else self.config.max_results

    @classmethod
    def is_enabled(cls) -> bool:
        env = cls.config.api_key_env
        if env is None:
            return True
        return bool(os.environ.get(env, "").strip())

    @property
    def name(self) -> str:
        return self.config.name

    @abc.abstractmethod
    async def search(self, query: str, query_variant: str = "") -> list[SearchResult]:
        """Run a single search query and return normalized-ish hits."""
        ...
