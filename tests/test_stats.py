"""Tests for plocate.stats."""

import logging

import plocate.database
import plocate.stats

_LOGGER = logging.getLogger(__name__)


def test_collect_statistics(minimal_database_path):
    """Collect summary statistics from a synthetic fixture database."""

    with plocate.database.PlocateDatabase.open(minimal_database_path) as database:
        statistics = plocate.stats.collect_statistics(database)

    assert statistics.path_count == 3
    assert statistics.num_docids == 1
    assert statistics.version == 1
    assert statistics.configuration_entries["prune_bind_mounts"] == ["0"]
    assert statistics.compressed_filename_bytes > 0


def test_collect_statistics_from_updatedb_database(updatedb_database_path):
    """Collect summary statistics from the updatedb fixture database."""

    with plocate.database.PlocateDatabase.open(updatedb_database_path) as database:
        statistics = plocate.stats.collect_statistics(database)

    assert statistics.path_count == 104
    assert statistics.num_docids == 4
    assert statistics.version == 1
    assert statistics.max_version == 2
    assert statistics.check_visibility is True
    assert "prune_bind_mounts" in statistics.configuration_entries
    assert statistics.compressed_filename_bytes > 0


def test_compressed_filename_byte_count():
    """Compute compressed filename bytes from block offsets."""

    offsets = (100, 150, 220)
    byte_count = plocate.stats.compressed_filename_byte_count(offsets, 2)
    assert byte_count == 120


def test_count_paths(minimal_database_path):
    """Count indexed paths in a synthetic fixture database."""

    with plocate.database.PlocateDatabase.open(minimal_database_path) as database:
        path_count = plocate.stats.count_paths(database)
        assert path_count == 3


def test_count_paths_in_updatedb_database(updatedb_database_path):
    """Count indexed paths in the updatedb fixture database."""

    with plocate.database.PlocateDatabase.open(updatedb_database_path) as database:
        path_count = plocate.stats.count_paths(database)
        assert path_count == 104
