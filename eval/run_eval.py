#!/usr/bin/env python3
"""Eval harness: per-provider recall, unique contributions, marginal gain."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml

from meta_search.normalize import canonicalize_url
from meta_search.providers import get_enabled_providers
from meta_search.providers.base import SearchProvider


def _load_queries(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text())
    return data.get("queries") or []


async def _search_provider(provider: SearchProvider, query: str) -> set[str]:
    try:
        hits = await provider.search(query)
        return {canonicalize_url(h.url) for h in hits if h.url}
    except Exception:
        return set()


async def eval_one(
    entry: dict,
    providers: list[SearchProvider],
    timeout: float,
) -> dict:
    query = entry["query"]
    relevant = {canonicalize_url(u) for u in entry.get("relevant_urls") or []}
    n_rel = len(relevant) or 1

    per_provider: dict[str, set[str]] = {}
    for p in providers:
        p._timeout = timeout
        per_provider[p.name] = await _search_provider(p, query)

    recalls = {name: len(urls & relevant) / n_rel for name, urls in per_provider.items()}

    union: set[str] = set()
    provider_order = sorted(per_provider.keys())
    cumulative: list[dict] = []
    for name in provider_order:
        before = len(union & relevant)
        union |= per_provider[name]
        after = len(union & relevant)
        marginal = (after - before) / n_rel
        cumulative.append(
            {
                "provider": name,
                "recall_solo": recalls[name],
                "marginal_recall_gain": marginal,
                "cumulative_recall": after / n_rel,
            }
        )

    unique_contrib = {}
    for name, urls in per_provider.items():
        others = set().union(*(u for n, u in per_provider.items() if n != name))
        unique_contrib[name] = sorted(urls - others)

    precision_proxy = {}
    for name, urls in per_provider.items():
        if not urls:
            precision_proxy[name] = 0.0
        else:
            precision_proxy[name] = len(urls & relevant) / len(urls)

    return {
        "id": entry.get("id"),
        "query": query,
        "relevant_count": len(relevant),
        "per_provider_recall": recalls,
        "per_provider_precision_proxy": precision_proxy,
        "unique_urls_by_provider": {k: len(v) for k, v in unique_contrib.items()},
        "marginal_gain_sequence": cumulative,
    }


async def run_eval(queries_path: Path, timeout: float) -> dict:
    queries = _load_queries(queries_path)
    providers = get_enabled_providers()
    if not providers:
        print("No hay proveedores habilitados.", file=sys.stderr)
        return {"error": "no_providers"}

    results = []
    for entry in queries:
        results.append(await eval_one(entry, providers, timeout))

    agg_recall: dict[str, list[float]] = {p.name: [] for p in providers}
    for r in results:
        for name, rec in r["per_provider_recall"].items():
            agg_recall[name].append(rec)

    summary = {
        "providers": [p.name for p in providers],
        "mean_recall_by_provider": {
            k: (sum(v) / len(v) if v else 0.0) for k, v in agg_recall.items()
        },
        "queries": results,
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluar recall y ganancia marginal por proveedor")
    parser.add_argument(
        "--queries",
        type=Path,
        default=Path(__file__).parent / "queries.yaml",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    summary = asyncio.run(run_eval(args.queries, args.timeout))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if "error" not in summary else 1


if __name__ == "__main__":
    raise SystemExit(main())
