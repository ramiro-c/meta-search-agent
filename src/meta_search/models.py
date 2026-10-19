from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Normalized search hit from a single provider."""

    url: str
    title: str
    snippet: str
    published: datetime | None = None
    provider: str
    rank: int = Field(ge=1, description="1-based rank within provider result list")
    query_variant: str = ""

    def model_dump_json_ready(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        return data


class FusedResult(BaseModel):
    """Result after deduplication and rank fusion."""

    url: str
    title: str
    snippet: str
    published: datetime | None = None
    providers: list[str] = Field(default_factory=list)
    provider_ranks: dict[str, int] = Field(default_factory=dict)
    rrf_score: float = 0.0
    relevance_score: float | None = None
    judge_notes: str | None = None

    def model_dump_json_ready(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class SearchResponse(BaseModel):
    query: str
    query_variants: list[str]
    providers_used: list[str]
    providers_failed: list[str] = Field(default_factory=list)
    results: list[FusedResult]
    raw_count: int = 0
    fused_count: int = 0

    def model_dump_json_ready(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
