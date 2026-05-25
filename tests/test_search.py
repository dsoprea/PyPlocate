import pytest

from plocate_db.search import SearchOptions, search_paths


def test_search_paths_substring():
    paths = [
        "/tmp/example/.catalog-repository.yaml",
        "/tmp/example/readme.txt",
    ]
    matches = list(search_paths(iter(paths), ".catalog-repository.yaml"))
    assert matches == ["/tmp/example/.catalog-repository.yaml"]


def test_search_paths_respects_limit():
    paths = ["/a/one.txt", "/a/two.txt", "/a/three.txt"]
    options = SearchOptions(limit=2)
    matches = list(search_paths(iter(paths), ".txt", options=options))
    assert matches == ["/a/one.txt", "/a/two.txt"]


def test_search_paths_requires_patterns():
    with pytest.raises(ValueError, match="at least one search pattern"):
        list(search_paths(iter(["/a"]), ))
