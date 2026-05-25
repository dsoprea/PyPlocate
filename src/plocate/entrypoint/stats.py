"""Print statistics about a plocate database."""

import argparse
import json
import sys

import plocate.constants
import plocate.database
import plocate.errors
import plocate.formatting



def _build_parser() -> argparse.ArgumentParser:
    """Build the pl_stats argument parser."""

    parser = argparse.ArgumentParser(description="Print statistics about a plocate database.")
    parser.add_argument(
        "database",
        nargs="?",
        default=plocate.constants.DEFAULT_DATABASE_PATH,
        help="path to plocate.db (default: {default_path})".format(
            default_path=plocate.constants.DEFAULT_DATABASE_PATH,
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print statistics as JSON",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse argv, collect database statistics, and print them."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)

    # Open the database and collect summary statistics.
    try:
        with plocate.database.PlocateDatabase.open(arguments.database) as database:
            statistics = database.statistics()
    except (plocate.errors.PlocateDatabaseError, OSError) as error:
        message = "pl_stats: {error}".format(error=error)
        print(message, file=sys.stderr)

        sys.exit(1)

    # Render statistics as JSON or human-readable text.
    if arguments.json:
        statistics_mapping = statistics.to_dict()
        print(json.dumps(statistics_mapping, indent=2, sort_keys=True))
    else:
        text = plocate.formatting.format_statistics_text(statistics)
        print(text)

    sys.exit(0)


if __name__ == "__main__":
    main()
