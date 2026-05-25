from plocate_db.database import PlocateDatabase
from plocate_db.stats import collect_statistics, compressed_filename_byte_count, count_paths


def test_collect_statistics(minimal_database_path):
    with PlocateDatabase.open(str(minimal_database_path)) as database:
        statistics = collect_statistics(database)

    assert statistics.path_count == 3
    assert statistics.num_docids == 1
    assert statistics.version == 1
    assert statistics.configuration_entries["prune_bind_mounts"] == ["0"]
    assert statistics.compressed_filename_bytes > 0


def test_compressed_filename_byte_count():
    offsets = (100, 150, 220)
    assert compressed_filename_byte_count(offsets, 2) == 120


def test_count_paths(minimal_database_path):
    with PlocateDatabase.open(str(minimal_database_path)) as database:
        assert count_paths(database) == 3
