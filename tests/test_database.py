"""Tests for plocate.database."""

import logging
import os

import pytest

import plocate.database
import plocate.errors
import plocate.search

_LOGGER = logging.getLogger(__name__)


def test_open_minimal_database(minimal_database_path):
    """Open a minimal fixture database and iterate its paths."""

    with plocate.database.PlocateDatabase.open(minimal_database_path) as database:
        assert database.header.num_docids == 1
        path_iterator = database.iter_paths()
        indexed_paths = list(path_iterator)
        assert indexed_paths == [
            "/tmp/example/.catalog-repository.yaml",
            "/tmp/example/readme.txt",
            "/var/log/syslog",
        ]


def test_read_configuration_block(minimal_database_path):
    """Read updatedb configuration entries from a fixture database."""

    with plocate.database.PlocateDatabase.open(minimal_database_path) as database:
        entries = database.read_configuration_block()
        assert [entry.name for entry in entries] == ["prune_bind_mounts", "prunepaths"]


def test_search_database(minimal_database_path):
    """Search a fixture database for matching paths."""

    with plocate.database.PlocateDatabase.open(minimal_database_path) as database:
        match_iterator = plocate.search.search_database(database, ".catalog-repository.yaml")
        matches = list(match_iterator)
    assert matches == ["/tmp/example/.catalog-repository.yaml"]


def test_iter_indexed_entries_pairs_directory_metadata(directory_timed_database_path):
    """Pair indexed paths with directory timestamp metadata."""

    with plocate.database.PlocateDatabase.open(directory_timed_database_path) as database:
        indexed_entries = list(database.iter_indexed_entries())
    assert indexed_entries[0].path == "/tmp/example"
    assert indexed_entries[0].directory_time is not None
    assert indexed_entries[0].directory_time.is_directory is True
    assert indexed_entries[1].directory_time is not None
    assert indexed_entries[1].directory_time.is_directory is False


def test_rejects_invalid_database(tmp_path):
    """Reject files that are not valid plocate databases."""

    invalid_path = os.path.join(str(tmp_path), "invalid.db")
    with open(invalid_path, "wb") as invalid_file:
        invalid_file.write(b"not a database")

    with pytest.raises(plocate.errors.PlocateFormatError):
        with plocate.database.PlocateDatabase.open(invalid_path):
            pass
