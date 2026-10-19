from meta_search.dedup import deduplicate_results
from meta_search.models import SearchResult


def test_dedup_keeps_better_rank():
    a = SearchResult(
        url="https://example.com/x",
        title="A",
        snippet="s",
        provider="p",
        rank=3,
    )
    b = SearchResult(
        url="https://example.com/x",
        title="B better title",
        snippet="s",
        provider="p",
        rank=1,
    )
    out = deduplicate_results([a, b])
    assert len(out) == 1
    assert out[0].rank == 1
    assert out[0].title == "B better title"


def test_dedup_different_urls():
    a = SearchResult(url="https://a.com", title="a", snippet="", provider="p", rank=1)
    b = SearchResult(url="https://b.com", title="b", snippet="", provider="p", rank=1)
    assert len(deduplicate_results([a, b])) == 2
