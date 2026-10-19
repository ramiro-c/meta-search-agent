from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx

from meta_search.models import SearchResult
from meta_search.providers.base import ProviderConfig, SearchProvider


class BraveProvider(SearchProvider):
    config = ProviderConfig(name="brave", api_key_env="BRAVE_API_KEY")

    async def search(self, query: str, query_variant: str = "") -> list[SearchResult]:
        key = os.environ["BRAVE_API_KEY"]
        url = "https://api.search.brave.com/res/v1/web/search"
        params = {"q": query, "count": self._max_results}
        headers = {"Accept": "application/json", "X-Subscription-Token": key}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        web = data.get("web", {}) or {}
        items: list[dict[str, Any]] = web.get("results") or []
        out: list[SearchResult] = []
        for i, item in enumerate(items[: self._max_results], start=1):
            published = _parse_date(item.get("page_age") or item.get("age"))
            out.append(
                SearchResult(
                    url=item.get("url") or "",
                    title=item.get("title") or "",
                    snippet=item.get("description") or "",
                    published=published,
                    provider=self.name,
                    rank=i,
                    query_variant=query_variant or query,
                )
            )
        return out


def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
