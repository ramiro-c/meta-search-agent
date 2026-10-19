from __future__ import annotations

import json
import os
import re

import httpx

_OR_SPLIT = re.compile(r"\s+OR\s+", re.IGNORECASE)


def split_or_query(query: str) -> list[str]:
    """Split boolean OR queries into separate search strings."""
    parts = _OR_SPLIT.split(query.strip())
    if len(parts) <= 1:
        return [query.strip()]
    return [p.strip() for p in parts if p.strip()]


async def expand_query_variants(
    query: str,
    *,
    use_llm: bool = False,
    max_variants: int = 3,
) -> list[str]:
    """
    Return query variants: base query plus OR splits, optionally LLM rewrites.
    """
    variants: list[str] = []
    seen: set[str] = set()

    def add(q: str) -> None:
        q = q.strip()
        if q and q.lower() not in seen:
            seen.add(q.lower())
            variants.append(q)

    add(query)
    for part in split_or_query(query):
        add(part)

    if use_llm:
        llm_variants = await _llm_query_variants(query, max_variants=max_variants)
        for v in llm_variants:
            add(v)

    return variants


async def _llm_query_variants(query: str, max_variants: int) -> list[str]:
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return []
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    prompt = (
        f"Generá hasta {max_variants} reformulaciones de búsqueda web distintas "
        f"para encontrar información sobre: {query}\n"
        "Respondé solo con un JSON array de strings, sin markdown."
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content.strip())
            if isinstance(parsed, list):
                return [str(x) for x in parsed[:max_variants]]
    except Exception:
        return []
    return []
