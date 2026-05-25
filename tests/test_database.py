import pytest

from plocate_db.database import PlocateDatabase
from plocate_db.errors import PlocateFormatError
from plocate_db.search import search_database


def test_open_minimal_database(minimal_database_path):
    with PlocateDatabase.open(str(minimal_database_path)) as database:
        assert database.header.num_docids == 1
        assert list(database.iter_paths()) == [
            "/tmp/example/.catalog-repository.yaml",
            "/tmp/example/readme.txt",
            "/var/log/syslog",
        ]


def test_read_configuration_block(minimal_database_path):
    with PlocateDatabase.open(str(minimal_database_path)) as database:
        entries = database.read_configuration_block()
        assert [entry.name for entry in entries] == ["prune_bind_mounts", "prunepaths"]


def test_search_database(minimal_database_path):
    with PlocateDatabase.open(str(minimal_database_path)) as database:
        matches = list(search_database(database, ".catalog-repository.yaml"))
    assert matches == ["/tmp/example/.catalog-repository.yaml"]


def test_rejects_invalid_database(tmp_path):
    invalid_path = tmp_path / "invalid.db"
    invalid_path.write_bytes(b"not a database")

    with pytest.raises(PlocateFormatError):
        with PlocateDatabase.open(str(invalid_path)) as database:
            database.header
