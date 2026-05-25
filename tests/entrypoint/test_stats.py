"""Tests for plocate.entrypoint.stats."""

import json
import logging
import os

import pytest

import plocate.entrypoint.stats

_LOGGER = logging.getLogger(__name__)


def test_pl_stats_human_output(minimal_database_path, capsys):
    """Print human-readable statistics for a fixture database."""

    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.stats.main([minimal_database_path])
    assert exit_info.value.code == 0

    captured = capsys.readouterr()
    assert "indexed paths: 3" in captured.out
    assert "prune_bind_mounts: 0" in captured.out


def test_pl_stats_json_output(minimal_database_path, capsys):
    """Print JSON statistics for a fixture database."""

    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.stats.main([minimal_database_path, "--json"])
    assert exit_info.value.code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["path_count"] == 3
    assert payload["configuration_entries"]["prunepaths"] == ["/tmp"]


def test_pl_stats_reports_missing_database(tmp_path, capsys):
    """Exit with a non-zero status when the database file is missing."""

    missing_path = os.path.join(str(tmp_path), "missing.db")
    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.stats.main([missing_path])
    assert exit_info.value.code == 1
    assert "pl_stats:" in capsys.readouterr().err
