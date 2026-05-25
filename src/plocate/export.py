"""Export indexed paths from a plocate database."""

import collections.abc
import dataclasses
import fnmatch
import json

import plocate.indexed_entry



@dataclasses.dataclass(frozen=True, slots=True)
class ExportRecord:
    """One indexed path exported from a plocate database."""

    path: str
    docid: int
    block_index: int
    database_version: int
    max_version: int
    check_visibility: bool
    is_directory: bool | None = None
    directory_time_seconds: int | None = None
    directory_time_nanoseconds: int | None = None

    @classmethod
    def from_indexed_entry(cls, indexed_entry: plocate.indexed_entry.IndexedEntry) -> ExportRecord:
        """Build an export record from one indexed database entry."""

        is_directory = None
        directory_time_seconds = None
        directory_time_nanoseconds = None
        if indexed_entry.directory_time is not None:
            is_directory = indexed_entry.directory_time.is_directory
            if indexed_entry.directory_time.is_directory:
                directory_time_seconds = indexed_entry.directory_time.seconds
                directory_time_nanoseconds = indexed_entry.directory_time.nanoseconds

        record = cls(
            path=indexed_entry.path,
            docid=indexed_entry.docid,
            block_index=indexed_entry.block_index,
            database_version=indexed_entry.database_version,
            max_version=indexed_entry.max_version,
            check_visibility=indexed_entry.check_visibility,
            is_directory=is_directory,
            directory_time_seconds=directory_time_seconds,
            directory_time_nanoseconds=directory_time_nanoseconds,
        )

        return record

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable mapping for this record."""

        mapping: dict[str, object] = {
            "path": self.path,
            "docid": self.docid,
            "block_index": self.block_index,
            "database_version": self.database_version,
            "max_version": self.max_version,
            "check_visibility": self.check_visibility,
        }
        if self.is_directory is not None:
            mapping["is_directory"] = self.is_directory
        if self.directory_time_seconds is not None:
            mapping["directory_time_seconds"] = self.directory_time_seconds
        if self.directory_time_nanoseconds is not None:
            mapping["directory_time_nanoseconds"] = self.directory_time_nanoseconds

        return mapping


@dataclasses.dataclass(slots=True)
class ExportOptions:
    """Options controlling plocate database export."""

    include_pattern: str | None = None


def _path_matches_include_pattern(path: str, include_pattern: str) -> bool:
    """Return whether path matches an fnmatch include pattern."""

    matched = fnmatch.fnmatch(path, include_pattern)

    return matched


def iter_export_records(
    database,
    *,
    options: ExportOptions | None = None,
) -> collections.abc.Iterator[ExportRecord]:
    """Yield export records for every indexed path in database order."""

    if options is None:
        export_options = ExportOptions()
    else:
        export_options = options

    # Walk indexed entries and apply the optional include filter.
    indexed_entry_iterator = database.iter_indexed_entries()
    for indexed_entry in indexed_entry_iterator:
        if export_options.include_pattern is not None:
            matched = _path_matches_include_pattern(indexed_entry.path, export_options.include_pattern)
            if not matched:
                continue

        record = ExportRecord.from_indexed_entry(indexed_entry)
        yield record


def format_export_record_jsonl(record: ExportRecord) -> str:
    """Format one export record as a JSON Lines row."""

    mapping = record.to_dict()
    line = json.dumps(mapping, sort_keys=True)
    formatted = line + "\n"

    return formatted
