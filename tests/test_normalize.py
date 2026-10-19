from meta_search.normalize import canonicalize_url, normalize_result
from meta_search.models import SearchResult


def test_canonicalize_strips_tracking_and_www():
    url = "https://www.example.com/path/?utm_source=x&b=2&a=1"
    assert canonicalize_url(url) == "https://example.com/path?a=1&b=2"


def test_canonicalize_trailing_slash():
    assert canonicalize_url("https://example.com/foo/") == "https://example.com/foo"


def test_normalize_result_cleans_whitespace():
    r = SearchResult(
        url="https://example.com",
        title="  Hello   world ",
        snippet="line1\n\nline2",
        provider="test",
        rank=1,
    )
    n = normalize_result(r)
    assert n.title == "Hello world"
    assert n.snippet == "line1 line2"
