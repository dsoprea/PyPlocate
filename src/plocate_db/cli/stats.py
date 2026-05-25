"""Print statistics about a plocate database."""

from __future__ import annotations

import argparse
import json
import sys

from plocate_db.constants import DEFAULT_DATABASE_PATH
from plocate_db.database import PlocateDatabase
from plocate_db.errors import PlocateDatabaseError
from plocate_db.formatting import format_statistics_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print statistics about a plocate database.")
    parser.add_argument(
        "database",
        nargs="?",
        default=DEFAULT_DATABASE_PATH,
        help=f"path to plocate.db (default: {DEFAULT_DATABASE_PATH})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print statistics as JSON",
    )
    return parser


def run(arguments: argparse.Namespace) -> int:
    try:
        with PlocateDatabase.open(arguments.database) as database:
            statistics = database.statistics()
    except (PlocateDatabaseError, OSError) as error:
        print(f"pl_stats: {error}", file=sys.stderr)
        return 1

    if arguments.json:
        print(json.dumps(statistics.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_statistics_text(statistics))

    return 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
