from __future__ import annotations

import json
import os

import httpx

from meta_search.models import FusedResult


async def llm_judge(
    query: str,
    results: list[FusedResult],
    *,
    top_k: int = 10,
) -> list[FusedResult]:
    """
    Score relevance with an OpenAI-compatible chat API. No-op if no API key.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or not results:
        return results

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    candidates = results[:top_k]
    items = [
        {"i": i, "url": r.url, "title": r.title, "snippet": (r.snippet or "")[:400]}
        for i, r in enumerate(candidates)
    ]
    prompt = (
        f"Query: {query}\n\n"
        "Para cada resultado, asigná relevance_score entre 0 y 1 "
        "(1 = muy relevante). Opcional: notes breves.\n"
        f"Resultados: {json.dumps(items, ensure_ascii=False)}\n\n"
        'Respondé JSON: {"scores": [{"i": 0, "relevance_score": 0.9, "notes": "..."}, ...]}'
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            payload = json.loads(_strip_json_fence(content))
    except Exception:
        return results

    scores_map: dict[int, tuple[float, str | None]] = {}
    for entry in payload.get("scores") or []:
        try:
            idx = int(entry["i"])
            score = float(entry["relevance_score"])
            notes = entry.get("notes")
            scores_map[idx] = (max(0.0, min(1.0, score)), notes)
        except (KeyError, TypeError, ValueError):
            continue

    judged: list[FusedResult] = []
    for i, r in enumerate(candidates):
        if i in scores_map:
            score, notes = scores_map[i]
            judged.append(
                r.model_copy(update={"relevance_score": score, "judge_notes": notes})
            )
        else:
            judged.append(r)
    judged.sort(
        key=lambda x: (x.relevance_score if x.relevance_score is not None else -1, x.rrf_score),
        reverse=True,
    )
    return judged + results[top_k:]


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text
