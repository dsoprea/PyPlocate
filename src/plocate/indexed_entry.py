"""Indexed path entries with database metadata."""

import dataclasses
import logging

import plocate.directory_data

_LOGGER = logging.getLogger(__name__)


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
