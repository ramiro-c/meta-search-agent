from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx

from meta_search.models import SearchResult
from meta_search.providers.base import ProviderConfig, SearchProvider


class TavilyProvider(SearchProvider):
    config = ProviderConfig(name="tavily", api_key_env="TAVILY_API_KEY")

    async def search(self, query: str, query_variant: str = "") -> list[SearchResult]:
        key = os.environ["TAVILY_API_KEY"]
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": key,
            "query": query,
            "max_results": self._max_results,
            "include_answer": False,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        items: list[dict[str, Any]] = data.get("results") or []
        out: list[SearchResult] = []
        for i, item in enumerate(items[: self._max_results], start=1):
            published = None
            if item.get("published_date"):
                try:
                    published = datetime.fromisoformat(
                        str(item["published_date"]).replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            out.append(
                SearchResult(
                    url=item.get("url") or "",
                    title=item.get("title") or "",
                    snippet=item.get("content") or "",
                    published=published,
                    provider=self.name,
                    rank=i,
                    query_variant=query_variant or query,
                )
            )
        return out
