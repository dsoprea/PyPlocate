"""Tests for plocate.export."""

import json

import plocate.database
import plocate.export



def _minimal_export_payload(path: str, block_index: int) -> dict[str, object]:
    """Build the expected export payload for the minimal fixture database."""

    payload = {
        "block_index": block_index,
        "check_visibility": False,
        "database_version": 1,
        "docid": 0,
        "max_version": 2,
        "path": path,
    }

    return payload


def test_iter_export_records_yields_every_path(minimal_database_path):
    """Export every indexed path from a synthetic fixture database."""

    with plocate.database.PlocateDatabase.open(minimal_database_path) as database:
        record_iterator = plocate.export.iter_export_records(database)
        records = list(record_iterator)
    assert [record.path for record in records] == [
        "/tmp/example/.catalog-repository.yaml",
        "/tmp/example/readme.txt",
        "/var/log/syslog",
    ]
    assert records[0].docid == 0
    assert records[0].block_index == 0
    assert records[2].block_index == 2


def test_iter_export_records_yields_updatedb_paths(updatedb_database_path):
    """Export indexed paths from the updatedb fixture database."""

    with plocate.database.PlocateDatabase.open(updatedb_database_path) as database:
        record_iterator = plocate.export.iter_export_records(database)
        records = list(record_iterator)
    assert len(records) == 104
    assert records[0].docid == 0
    assert records[0].check_visibility is True
    assert any(record.path.endswith("/pyproject.toml") for record in records)


def test_iter_export_records_includes_directory_metadata(directory_timed_database_path):
    """Export directory timestamp metadata when the database stores it."""

    with plocate.database.PlocateDatabase.open(directory_timed_database_path) as database:
        record_iterator = plocate.export.iter_export_records(database)
        records = list(record_iterator)
    assert records[0].is_directory is True
    assert records[0].directory_time_seconds == 1700000000
    assert records[0].directory_time_nanoseconds == 123456789
    assert records[1].is_directory is False
    assert records[1].directory_time_seconds is None
    assert records[1].directory_time_nanoseconds is None


def test_iter_export_records_filters_with_include_pattern(minimal_database_path):
    """Export only paths that match the configured fnmatch include pattern."""

    options = plocate.export.ExportOptions(include_pattern="/tmp/example/*")
    with plocate.database.PlocateDatabase.open(minimal_database_path) as database:
        record_iterator = plocate.export.iter_export_records(database, options=options)
        records = list(record_iterator)
    assert [record.path for record in records] == [
        "/tmp/example/.catalog-repository.yaml",
        "/tmp/example/readme.txt",
    ]


def test_format_export_record_jsonl(minimal_database_path):
    """Format one export record as a JSON Lines row."""

    with plocate.database.PlocateDatabase.open(minimal_database_path) as database:
        record_iterator = plocate.export.iter_export_records(database)
        first_record = next(record_iterator)
    formatted = plocate.export.format_export_record_jsonl(first_record)
    payload = json.loads(formatted)
    assert payload == _minimal_export_payload("/tmp/example/.catalog-repository.yaml", 0)
    assert formatted.endswith("\n")
