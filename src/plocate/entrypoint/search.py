"""Search a plocate database for paths."""

import argparse
import logging
import sys

import plocate.database
import plocate.errors
import plocate.formatting
import plocate.search

_LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the pl_search argument parser."""

    parser = argparse.ArgumentParser(description="Search for paths in a plocate database.")
    parser.add_argument(
        "database",
        help="path to plocate.db",
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
    search_mode_group = parser.add_mutually_exclusive_group()
    search_mode_group.add_argument(
        "--indexed",
        action="store_true",
        help="force trigram-index search",
    )
    search_mode_group.add_argument(
        "--scan",
        action="store_true",
        help="force a full scan of every filename block",
    )

    return parser


def build_search_options(arguments: argparse.Namespace) -> plocate.search.SearchOptions:
    """Translate parsed CLI arguments into search options."""

    use_regex = arguments.regexp or arguments.regex
    options = plocate.search.SearchOptions(
        ignore_case=arguments.ignore_case,
        match_basename=arguments.basename,
        use_regex=use_regex,
        extended_regex=arguments.regex,
        limit=arguments.limit,
        force_indexed_search=arguments.indexed,
        force_linear_search=arguments.scan,
    )

    return options


def main(argv: list[str] | None = None) -> None:
    """Parse argv, search the database, and print matches or a count."""

    parser = build_parser()
    arguments = parser.parse_args(argv)
    options = build_search_options(arguments)

    # Open the database and collect matching paths.
    try:
        with plocate.database.PlocateDatabase.open(arguments.database) as database:
            match_iterator = plocate.search.search_database(database, *arguments.patterns, options=options)
            matches = list(match_iterator)
    except (plocate.errors.PlocateDatabaseError, OSError, ValueError) as error:
        message = "pl_search: {error}".format(error=error)
        print(message, file=sys.stderr)

        sys.exit(1)

    # Print only the match count when requested.
    if arguments.count:
        print(len(matches))
        if matches:
            sys.exit(0)

        sys.exit(1)

    # Write formatted matches to stdout.
    formatted = plocate.formatting.format_search_matches(matches, use_null_separator=arguments.null)
    sys.stdout.write(formatted)
    if matches:
        sys.exit(0)

    sys.exit(1)


if __name__ == "__main__":
    main()
