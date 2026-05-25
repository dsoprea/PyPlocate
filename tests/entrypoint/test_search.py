"""Tests for plocate.entrypoint.search."""

import pytest

import plocate.entrypoint.search

import tests.support.updatedb_fixture



def test_pl_search_outputs_matches(updatedb_database_path, capsys):
    """Print matching paths from the updatedb fixture database."""

    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.search.main(
            [
                updatedb_database_path,
                tests.support.updatedb_fixture.UPDATEDB_PYPROJECT_PATTERN,
            ]
        )
    assert exit_info.value.code == 0
    captured = capsys.readouterr()
    assert "/pyproject.toml" in captured.out


def test_pl_search_count_mode(updatedb_database_path, capsys):
    """Print only the number of matches when count mode is enabled."""

    with pytest.raises(SystemExit) as exit_info:
        plocate.entrypoint.search.main(
            [
                updatedb_database_path,
                "-c",
                tests.support.updatedb_fixture.UPDATEDB_PYPROJECT_PATTERN,
            ]
        )
    assert exit_info.value.code == 0
    assert int(capsys.readouterr().out.strip()) >= 1


def test_pl_search_builds_options():
    """Translate CLI flags into search options."""

    parser = plocate.entrypoint.search._build_parser()
    arguments = parser.parse_args(
        ["/tmp/test.db", "-i", "-b", "--regex", "pattern"]
    )
    options = plocate.entrypoint.search._build_search_options(arguments)
    assert options.ignore_case is True
    assert options.match_basename is True
    assert options.use_regex is True


def test_pl_search_builds_force_search_mode_options():
    """Translate forced search mode flags into search options."""

    parser = plocate.entrypoint.search._build_parser()
    indexed_arguments = parser.parse_args(["/tmp/test.db", "--indexed", "pattern"])
    indexed_options = plocate.entrypoint.search._build_search_options(indexed_arguments)
    assert indexed_options.force_indexed_search is True
    assert indexed_options.force_linear_search is False

    scan_arguments = parser.parse_args(["/tmp/test.db", "--scan", "pattern"])
    scan_options = plocate.entrypoint.search._build_search_options(scan_arguments)
    assert scan_options.force_indexed_search is False
    assert scan_options.force_linear_search is True
