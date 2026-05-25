import json

from plocate_db.cli.search import build_parser as build_search_parser
from plocate_db.cli.search import build_search_options, run as run_search
from plocate_db.cli.stats import build_parser as build_stats_parser
from plocate_db.cli.stats import run as run_stats


def test_pl_stats_human_output(minimal_database_path, capsys):
    arguments = build_stats_parser().parse_args([str(minimal_database_path)])
    assert run_stats(arguments) == 0

    captured = capsys.readouterr()
    assert "indexed paths: 3" in captured.out
    assert "prune_bind_mounts: 0" in captured.out


def test_pl_stats_json_output(minimal_database_path, capsys):
    arguments = build_stats_parser().parse_args([str(minimal_database_path), "--json"])
    assert run_stats(arguments) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["path_count"] == 3
    assert payload["configuration_entries"]["prunepaths"] == ["/tmp"]


def test_pl_stats_reports_missing_database(tmp_path, capsys):
    missing_path = tmp_path / "missing.db"
    arguments = build_stats_parser().parse_args([str(missing_path)])
    assert run_stats(arguments) == 1
    assert "pl_stats:" in capsys.readouterr().err


def test_pl_search_outputs_matches(minimal_database_path, capsys):
    arguments = build_search_parser().parse_args(
        ["-d", str(minimal_database_path), ".catalog-repository.yaml"]
    )
    assert run_search(arguments) == 0
    assert capsys.readouterr().out == "/tmp/example/.catalog-repository.yaml\n"


def test_pl_search_count_mode(minimal_database_path, capsys):
    arguments = build_search_parser().parse_args(
        ["-d", str(minimal_database_path), "-c", "readme"]
    )
    assert run_search(arguments) == 0
    assert capsys.readouterr().out == "1\n"


def test_pl_search_builds_options():
    arguments = build_search_parser().parse_args(
        ["-d", "/tmp/test.db", "-i", "-b", "--regex", "pattern"]
    )
    options = build_search_options(arguments)
    assert options.ignore_case is True
    assert options.match_basename is True
    assert options.use_regex is True
