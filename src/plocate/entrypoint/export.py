"""Export indexed paths from a plocate database as JSON Lines."""

import argparse
import logging
import sys

import plocate.constants
import plocate.database
import plocate.errors
import plocate.export

_LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the pl_export argument parser."""

    parser = argparse.ArgumentParser(description="Export indexed paths from a plocate database as JSON Lines.")
    parser.add_argument(
        "database",
        nargs="?",
        default=plocate.constants.DEFAULT_DATABASE_PATH,
        help="path to plocate.db (default: {default_path})".format(
            default_path=plocate.constants.DEFAULT_DATABASE_PATH,
        ),
    )
    parser.add_argument(
        "--include",
        metavar="PATTERN",
        help="export only paths matching this fnmatch pattern",
    )

    return parser


def build_export_options(arguments: argparse.Namespace) -> plocate.export.ExportOptions:
    """Translate parsed CLI arguments into export options."""

    options = plocate.export.ExportOptions(
        include_pattern=arguments.include,
    )

    return options


def main(argv: list[str] | None = None) -> None:
    """Parse argv and print indexed paths as JSON Lines."""

    parser = build_parser()
    arguments = parser.parse_args(argv)
    options = build_export_options(arguments)

    # Open the database and stream matching export records.
    try:
        with plocate.database.PlocateDatabase.open(arguments.database) as database:
            record_iterator = plocate.export.iter_export_records(database, options=options)
            for record in record_iterator:
                line = plocate.export.format_export_record_jsonl(record)
                sys.stdout.write(line)
    except (plocate.errors.PlocateDatabaseError, OSError) as error:
        message = "pl_export: {error}".format(error=error)
        print(message, file=sys.stderr)

        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
