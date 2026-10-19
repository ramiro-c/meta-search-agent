from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from meta_search.models import SearchResult
from meta_search.normalize import canonicalize_url
from meta_search.providers.base import ProviderConfig, SearchProvider


class WikipediaProvider(SearchProvider):
    """Búsqueda key-free vía API MediaWiki (inglés por defecto)."""

    config = ProviderConfig(name="wikipedia", api_key_env=None)

    def __init__(
        self,
        timeout: float | None = None,
        max_results: int | None = None,
        lang: str = "en",
    ):
        super().__init__(timeout=timeout, max_results=max_results)
        self._lang = lang

    async def search(self, query: str, query_variant: str = "") -> list[SearchResult]:
        api = f"https://{self._lang}.wikipedia.org/w/api.php"
        params: dict[str, Any] = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": self._max_results,
            "format": "json",
        }
        headers = {
            "User-Agent": "meta-search-agent/0.1 (https://github.com/meta-search-agent; educational)",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
            resp = await client.get(api, params=params)
            resp.raise_for_status()
            data = resp.json()
        items = (data.get("query") or {}).get("search") or []
        out: list[SearchResult] = []
        for i, item in enumerate(items[: self._max_results], start=1):
            title = item.get("title") or ""
            page_url = canonicalize_url(
                f"https://{self._lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
            )
            snippet = _strip_html(item.get("snippet") or "")
            published = None
            if item.get("timestamp"):
                try:
                    published = datetime.fromisoformat(
                        str(item["timestamp"]).replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            out.append(
                SearchResult(
                    url=page_url,
                    title=title,
                    snippet=snippet,
                    published=published,
                    provider=self.name,
                    rank=i,
                    query_variant=query_variant or query,
                )
            )
        return out


def _strip_html(text: str) -> str:
    import re

    return re.sub(r"<[^>]+>", "", text)
