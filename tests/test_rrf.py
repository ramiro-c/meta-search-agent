from meta_search.fusion import RRF_K, reciprocal_rank_fusion
from meta_search.models import SearchResult


def _hit(url: str, rank: int, provider: str = "p") -> SearchResult:
    return SearchResult(
        url=url,
        title=url,
        snippet="",
        provider=provider,
        rank=rank,
    )


def test_rrf_combines_providers():
    lists = {
        "a": [_hit("https://common.com", 1, "a"), _hit("https://only-a.com", 2, "a")],
        "b": [_hit("https://common.com", 2, "b"), _hit("https://only-b.com", 1, "b")],
    }
    fused = reciprocal_rank_fusion(lists, k=60)
    assert fused[0].url == "https://common.com"
    assert set(fused[0].providers) == {"a", "b"}
    assert fused[0].rrf_score == 1 / (RRF_K + 1) + 1 / (RRF_K + 2)


def test_rrf_single_list_order():
    lists = {"x": [_hit("https://first.com", 1), _hit("https://second.com", 2)]}
    fused = reciprocal_rank_fusion(lists, k=60)
    assert fused[0].url == "https://first.com"
    assert fused[1].url == "https://second.com"
    assert fused[0].rrf_score > fused[1].rrf_score
