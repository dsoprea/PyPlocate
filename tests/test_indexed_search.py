"""Tests for indexed plocate search."""

import pytest

import plocate.database
import plocate.errors
import plocate.search

import tests.support.updatedb_fixture



def test_search_database_uses_trigram_index(updatedb_database_path):
    """Find matches through the trigram hash table in an updatedb fixture."""

    with plocate.database.PlocateDatabase.open(updatedb_database_path) as database:
        assert database.has_trigram_index() is True
        match_iterator = plocate.search.search_database(
            database,
            tests.support.updatedb_fixture.UPDATEDB_PYPROJECT_PATTERN,
        )
        matches = list(match_iterator)
    assert any(match.endswith("/pyproject.toml") for match in matches)


def test_search_database_decodes_updatedb_posting_lists(updatedb_database_path):
    """Decode compact posting lists from an updatedb fixture database."""

    with plocate.database.PlocateDatabase.open(updatedb_database_path) as database:
        match_iterator = plocate.search.search_database(
            database,
            tests.support.updatedb_fixture.UPDATEDB_PYC_PATTERN,
        )
        matches = list(match_iterator)
    assert len(matches) == 2
    assert all(tests.support.updatedb_fixture.UPDATEDB_PYC_PATTERN in match for match in matches)


def test_search_database_indexed_respects_limit(updatedb_database_path):
    """Stop indexed searches once the configured limit is reached."""

    options = plocate.search.SearchOptions(limit=1)
    with plocate.database.PlocateDatabase.open(updatedb_database_path) as database:
        match_iterator = plocate.search.search_database(
            database,
            tests.support.updatedb_fixture.UPDATEDB_PYPROJECT_PATTERN,
            options=options,
        )
        matches = list(match_iterator)
    assert len(matches) == 1


def test_search_database_force_indexed_search(updatedb_database_path):
    """Force trigram-index search on a healthy database."""

    options = plocate.search.SearchOptions(force_indexed_search=True)
    with plocate.database.PlocateDatabase.open(updatedb_database_path) as database:
        match_iterator = plocate.search.search_database(
            database,
            tests.support.updatedb_fixture.UPDATEDB_PYPROJECT_PATTERN,
            options=options,
        )
        matches = list(match_iterator)
    assert any(match.endswith("/pyproject.toml") for match in matches)


def test_search_database_force_linear_search(updatedb_database_path):
    """Force a full scan on a healthy database."""

    options = plocate.search.SearchOptions(force_linear_search=True)
    with plocate.database.PlocateDatabase.open(updatedb_database_path) as database:
        match_iterator = plocate.search.search_database(
            database,
            tests.support.updatedb_fixture.UPDATEDB_PYPROJECT_PATTERN,
            options=options,
        )
        matches = list(match_iterator)
    assert any(match.endswith("/pyproject.toml") for match in matches)


def test_search_database_force_linear_search_on_truncated_database(truncated_database_path):
    """Force a full scan when the trigram index is unreadable."""

    options = plocate.search.SearchOptions(force_linear_search=True)
    with plocate.database.PlocateDatabase.open(truncated_database_path) as database:
        assert database.has_trigram_index() is False
        match_iterator = plocate.search.search_database(database, "readme", options=options)
        matches = list(match_iterator)
    assert matches == ["/tmp/example/readme.txt"]


def test_search_database_force_indexed_search_requires_trigram_index(truncated_database_path):
    """Reject forced indexed search when the database has no readable index."""

    options = plocate.search.SearchOptions(force_indexed_search=True)
    with plocate.database.PlocateDatabase.open(truncated_database_path) as database:
        with pytest.raises(plocate.errors.PlocateDatabaseError, match="no trigram index"):
            list(plocate.search.search_database(database, "readme", options=options))


def test_search_database_force_indexed_search_rejects_regex(updatedb_database_path):
    """Reject forced indexed search combined with regex patterns."""

    options = plocate.search.SearchOptions(force_indexed_search=True, use_regex=True)
    with plocate.database.PlocateDatabase.open(updatedb_database_path) as database:
        with pytest.raises(ValueError, match="indexed search cannot be used with regex"):
            list(plocate.search.search_database(database, r"pyproject\.toml$", options=options))


def test_search_database_force_indexed_search_rejects_short_pattern(updatedb_database_path):
    """Reject forced indexed search when the pattern is too short to index."""

    options = plocate.search.SearchOptions(force_indexed_search=True)
    with plocate.database.PlocateDatabase.open(updatedb_database_path) as database:
        with pytest.raises(ValueError, match="too short for indexed search"):
            list(plocate.search.search_database(database, "py", options=options))


def test_search_options_rejects_conflicting_force_flags():
    """Reject search options that force both indexed and linear search."""

    options = plocate.search.SearchOptions(force_indexed_search=True, force_linear_search=True)
    with pytest.raises(ValueError, match="cannot force both"):
        options.validate_search_mode()
