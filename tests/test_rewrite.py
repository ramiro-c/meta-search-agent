from meta_search.rewrite import split_or_query


def test_split_or_query():
    assert split_or_query("foo OR bar") == ["foo", "bar"]
    assert split_or_query("single") == ["single"]
