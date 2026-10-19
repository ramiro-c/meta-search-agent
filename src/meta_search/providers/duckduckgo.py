from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import httpx

from meta_search.models import SearchResult
from meta_search.providers.base import ProviderConfig, SearchProvider


class DuckDuckGoProvider(SearchProvider):
    config = ProviderConfig(name="duckduckgo", api_key_env=None)

    async def search(self, query: str, query_variant: str = "") -> list[SearchResult]:
        try:
            hits = await asyncio.to_thread(self._search_sync, query)
        except Exception:
            hits = []
        if hits:
            return self._to_results(hits, query_variant or query)
        try:
            return await self._search_html_lite(query, query_variant or query)
        except Exception:
            return []

    def _search_sync(self, query: str) -> list[dict[str, Any]]:
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS  # type: ignore[no-redef]
            except ImportError:
                return []
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=self._max_results))

    def _to_results(self, items: list[dict[str, Any]], query_variant: str) -> list[SearchResult]:
        out: list[SearchResult] = []
        for i, item in enumerate(items[: self._max_results], start=1):
            published = None
            if item.get("date"):
                try:
                    published = datetime.fromisoformat(str(item["date"]))
                except ValueError:
                    pass
            out.append(
                SearchResult(
                    url=item.get("href") or item.get("url") or "",
                    title=item.get("title") or "",
                    snippet=item.get("body") or item.get("snippet") or "",
                    published=published,
                    provider=self.name,
                    rank=i,
                    query_variant=query_variant,
                )
            )
        return out

    async def _search_html_lite(self, query: str, query_variant: str) -> list[SearchResult]:
        """Fallback sin dependencias extra: DuckDuckGo HTML lite."""
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query}
        headers = {"User-Agent": "meta-search-agent/0.1"}
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            resp = await client.post(url, data=data, headers=headers)
            resp.raise_for_status()
            html = resp.text
        return _parse_ddg_html(html, self._max_results, query_variant)


def _parse_ddg_html(html: str, max_results: int, query_variant: str) -> list[SearchResult]:
    import re

    out: list[SearchResult] = []
    blocks = re.findall(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    for i, (href, title, snippet) in enumerate(blocks[:max_results], start=1):
        title_clean = re.sub(r"<[^>]+>", "", title).strip()
        snippet_clean = re.sub(r"<[^>]+>", "", snippet).strip()
        out.append(
            SearchResult(
                url=href,
                title=title_clean,
                snippet=snippet_clean,
                provider="duckduckgo",
                rank=i,
                query_variant=query_variant,
            )
        )
    return out
