from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx

from meta_search.models import SearchResult
from meta_search.providers.base import ProviderConfig, SearchProvider


class ExaProvider(SearchProvider):
    config = ProviderConfig(name="exa", api_key_env="EXA_API_KEY")

    async def search(self, query: str, query_variant: str = "") -> list[SearchResult]:
        key = os.environ["EXA_API_KEY"]
        url = "https://api.exa.ai/search"
        payload = {
            "query": query,
            "numResults": self._max_results,
            "type": "auto",
            "contents": {"text": {"maxCharacters": 500}},
        }
        headers = {"x-api-key": key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        results: list[dict[str, Any]] = data.get("results") or []
        out: list[SearchResult] = []
        for i, item in enumerate(results[: self._max_results], start=1):
            published = None
            if item.get("publishedDate"):
                try:
                    published = datetime.fromisoformat(
                        str(item["publishedDate"]).replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            snippet = item.get("text") or item.get("summary") or ""
            if len(snippet) > 500:
                snippet = snippet[:497] + "..."
            out.append(
                SearchResult(
                    url=item.get("url") or "",
                    title=item.get("title") or "",
                    snippet=snippet,
                    published=published,
                    provider=self.name,
                    rank=i,
                    query_variant=query_variant or query,
                )
            )
        return out
