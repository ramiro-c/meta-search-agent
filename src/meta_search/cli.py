from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from meta_search.search import search_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Meta-buscador para agentes: combina indexadores y fusiona resultados."
    )
    parser.add_argument("query", help="Consulta de búsqueda")
    parser.add_argument(
        "--providers",
        help="Lista separada por comas (ej: duckduckgo,brave). Por defecto: todos habilitados.",
    )
    parser.add_argument("--max-output", type=int, default=20)
    parser.add_argument("--max-per-provider", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--llm-rewrite", action="store_true", help="Variantes de query con LLM")
    parser.add_argument(
        "--no-llm-judge",
        action="store_true",
        help="Saltar el juez LLM de relevancia",
    )
    parser.add_argument(
        "--skip-cheap-filter",
        action="store_true",
        help="Saltar filtro heurístico barato",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    only = None
    if args.providers:
        only = [p.strip() for p in args.providers.split(",") if p.strip()]

    try:
        data = asyncio.run(
            search_json(
                args.query,
                providers_only=only,
                timeout=args.timeout,
                max_results_per_provider=args.max_per_provider,
                max_output=args.max_output,
                use_llm_rewrite=args.llm_rewrite,
                use_llm_judge=not args.no_llm_judge,
                skip_cheap_filter=args.skip_cheap_filter,
            )
        )
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
