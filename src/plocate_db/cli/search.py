"""Search a plocate database for paths."""

from __future__ import annotations

import argparse
import sys

from plocate_db.constants import DEFAULT_DATABASE_PATH
from plocate_db.database import PlocateDatabase
from plocate_db.errors import PlocateDatabaseError
from plocate_db.formatting import format_search_matches
from plocate_db.search import SearchOptions, search_database


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search for paths in a plocate database.")
    parser.add_argument(
        "-d",
        "--database",
        default=DEFAULT_DATABASE_PATH,
        help=f"path to plocate.db (default: {DEFAULT_DATABASE_PATH})",
    )
    parser.add_argument(
        "patterns",
        nargs="+",
        help="one or more search patterns",
    )
    parser.add_argument(
        "-b",
        "--basename",
        action="store_true",
        help="match only the basename of each path",
    )
    parser.add_argument(
        "-c",
        "--count",
        action="store_true",
        help="print only the number of matches",
    )
    parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="match case-insensitively",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        metavar="LIMIT",
        help="stop after LIMIT matches",
    )
    parser.add_argument(
        "-0",
        "--null",
        action="store_true",
        help="delimit matches with NUL instead of newline",
    )
    parser.add_argument(
        "-r",
        "--regexp",
        action="store_true",
        help="treat patterns as regular expressions",
    )
    parser.add_argument(
        "--regex",
        action="store_true",
        help="treat patterns as extended regular expressions",
    )
    return parser


def build_search_options(arguments: argparse.Namespace) -> SearchOptions:
    return SearchOptions(
        ignore_case=arguments.ignore_case,
        match_basename=arguments.basename,
        use_regex=arguments.regexp or arguments.regex,
        extended_regex=arguments.regex,
        limit=arguments.limit,
    )


def run(arguments: argparse.Namespace) -> int:
    options = build_search_options(arguments)

    try:
        with PlocateDatabase.open(arguments.database) as database:
            matches = list(search_database(database, *arguments.patterns, options=options))
    except (PlocateDatabaseError, OSError, ValueError) as error:
        print(f"pl_search: {error}", file=sys.stderr)
        return 1

    if arguments.count:
        print(len(matches))
        return 0 if matches else 1

    sys.stdout.write(format_search_matches(matches, use_null_separator=arguments.null))
    return 0 if matches else 1


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
