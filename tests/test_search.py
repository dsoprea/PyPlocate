"""Tests for plocate.search."""

import logging

import pytest

import plocate.search

_LOGGER = logging.getLogger(__name__)


def test_search_paths_substring():
    """Find paths that contain a substring pattern."""

    paths = [
        "/tmp/example/.catalog-repository.yaml",
        "/tmp/example/readme.txt",
    ]
    path_iterator = iter(paths)
    matches = list(plocate.search._search_paths(path_iterator, ".catalog-repository.yaml"))
    assert matches == ["/tmp/example/.catalog-repository.yaml"]


def test_search_paths_respects_limit():
    """Stop yielding matches once the configured limit is reached."""

    paths = ["/a/one.txt", "/a/two.txt", "/a/three.txt"]
    options = plocate.search.SearchOptions(limit=2)
    path_iterator = iter(paths)
    matches = list(plocate.search._search_paths(path_iterator, ".txt", options=options))
    assert matches == ["/a/one.txt", "/a/two.txt"]


def test_search_paths_requires_patterns():
    """Require at least one search pattern."""

    with pytest.raises(ValueError, match="at least one search pattern"):
        path_iterator = iter(["/a"])
        list(plocate.search._search_paths(path_iterator))
