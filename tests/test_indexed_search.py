"""Tests for indexed plocate search."""

import logging

import plocate.database
import plocate.search

_LOGGER = logging.getLogger(__name__)


def test_search_database_uses_trigram_index(minimal_database_path):
    """Find matches through the trigram hash table."""

    with plocate.database.PlocateDatabase.open(minimal_database_path) as database:
        assert database.has_trigram_index() is True
        match_iterator = plocate.search.search_database(database, "readme")
        matches = list(match_iterator)
    assert matches == ["/tmp/example/readme.txt"]


def test_search_database_indexed_respects_limit(minimal_database_path):
    """Stop indexed searches once the configured limit is reached."""

    options = plocate.search.SearchOptions(limit=1)
    with plocate.database.PlocateDatabase.open(minimal_database_path) as database:
        match_iterator = plocate.search.search_database(database, "example", options=options)
        matches = list(match_iterator)
    assert len(matches) == 1
