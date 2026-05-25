"""Indexed path entries with database metadata."""

import dataclasses

import plocate.directory_data



@dataclasses.dataclass(frozen=True, slots=True)
class IndexedEntry:
    """One indexed path and its associated database metadata."""

    path: str
    docid: int
    block_index: int
    database_version: int
    max_version: int
    check_visibility: bool
    directory_time: plocate.directory_data.DirectoryTimeEntry | None
