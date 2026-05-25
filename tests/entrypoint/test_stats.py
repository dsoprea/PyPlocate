"""Tests for plocate.entrypoint.stats."""

import json
import logging
import os

import pytest

import plocate.entrypoint.stats

_LOGGER = logging.getLogger(__name__)


def test_pl_stats_human_output(updatedb_database_path, capsys):
    """Print human-readable statistics for the updatedb fixture database."""

    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.stats.main([updatedb_database_path])
    assert exit_info.value.code == 0

    captured = capsys.readouterr()
    assert "indexed paths: 104" in captured.out
    assert "prune_bind_mounts:" in captured.out


def test_pl_stats_json_output(updatedb_database_path, capsys):
    """Print JSON statistics for the updatedb fixture database."""

    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.stats.main([updatedb_database_path, "--json"])
    assert exit_info.value.code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["path_count"] == 104
    assert payload["num_docids"] == 4
    assert "prunepaths" in payload["configuration_entries"]


def test_pl_stats_reports_missing_database(tmp_path, capsys):
    """Exit with a non-zero status when the database file is missing."""

    missing_path = os.path.join(str(tmp_path), "missing.db")
    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.stats.main([missing_path])
    assert exit_info.value.code == 1
    assert "pl_stats:" in capsys.readouterr().err
