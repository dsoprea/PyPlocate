"""Tests for plocate.entrypoint.export."""

import json
import logging
import os

import pytest

import plocate.entrypoint.export

_LOGGER = logging.getLogger(__name__)


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


def test_pl_export_outputs_jsonl(minimal_database_path, capsys):
    """Print every indexed path as JSON Lines."""

    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.export.main([minimal_database_path])
    assert exit_info.value.code == 0

    lines = capsys.readouterr().out.splitlines()
    payloads = [json.loads(line) for line in lines]
    assert payloads == [
        _minimal_export_payload("/tmp/example/.catalog-repository.yaml", 0),
        _minimal_export_payload("/tmp/example/readme.txt", 1),
        _minimal_export_payload("/var/log/syslog", 2),
    ]


def test_pl_export_outputs_directory_metadata(directory_timed_database_path, capsys):
    """Print directory timestamp metadata in JSON Lines export."""

    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.export.main([directory_timed_database_path])
    assert exit_info.value.code == 0

    lines = capsys.readouterr().out.splitlines()
    payloads = [json.loads(line) for line in lines]
    assert payloads[0]["path"] == "/tmp/example"
    assert payloads[0]["is_directory"] is True
    assert payloads[0]["directory_time_seconds"] == 1700000000
    assert payloads[0]["directory_time_nanoseconds"] == 123456789
    assert payloads[1]["is_directory"] is False
    assert "directory_time_seconds" not in payloads[1]


def test_pl_export_include_pattern(minimal_database_path, capsys):
    """Export only paths matching the --include fnmatch pattern."""

    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.export.main(
            [minimal_database_path, "--include", "/var/log/*"]
        )
    assert exit_info.value.code == 0

    lines = capsys.readouterr().out.splitlines()
    payloads = [json.loads(line) for line in lines]
    assert payloads == [_minimal_export_payload("/var/log/syslog", 2)]


def test_pl_export_reports_missing_database(tmp_path, capsys):
    """Exit with a non-zero status when the database file is missing."""

    missing_path = os.path.join(str(tmp_path), "missing.db")
    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.export.main([missing_path])
    assert exit_info.value.code == 1
    assert "pl_export:" in capsys.readouterr().err
