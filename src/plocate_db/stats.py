"""Database statistics collection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

from plocate_db.config import configuration_entries_to_mapping


@dataclass(frozen=True, slots=True)
class DatabaseStatistics:
    database_path: str | None
    file_size_bytes: int
    version: int
    max_version: int
    num_docids: int
    path_count: int
    hashtable_size: int
    extra_ht_slots: int
    hash_table_offset_bytes: int
    filename_index_offset_bytes: int
    compressed_filename_bytes: int
    zstd_dictionary_length_bytes: int
    directory_data_length_bytes: int
    next_zstd_dictionary_length_bytes: int
    conf_block_length_bytes: int
    check_visibility: bool
    configuration_entries: dict[str, list[str]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class StatisticsSource(Protocol):
    path: str | None
    file_size: int
    header: object

    def filename_block_offsets(self) -> tuple[int, ...]: ...
    def iter_filename_blocks(self): ...
    def read_configuration_block(self): ...


def compressed_filename_byte_count(offsets: tuple[int, ...], docid_count: int) -> int:
    if docid_count == 0:
        return 0
    return offsets[-1] - offsets[0]


def count_paths(database: StatisticsSource) -> int:
    return sum(len(block_paths) for block_paths in database.iter_filename_blocks())


def collect_statistics(database: StatisticsSource) -> DatabaseStatistics:
    offsets = database.filename_block_offsets()
    header = database.header

    return DatabaseStatistics(
        database_path=database.path,
        file_size_bytes=database.file_size,
        version=header.version,
        max_version=header.max_version,
        num_docids=header.num_docids,
        path_count=count_paths(database),
        hashtable_size=header.hashtable_size,
        extra_ht_slots=header.extra_ht_slots,
        hash_table_offset_bytes=header.hash_table_offset_bytes,
        filename_index_offset_bytes=header.filename_index_offset_bytes,
        compressed_filename_bytes=compressed_filename_byte_count(offsets, header.num_docids),
        zstd_dictionary_length_bytes=header.zstd_dictionary_length_bytes,
        directory_data_length_bytes=header.directory_data_length_bytes,
        next_zstd_dictionary_length_bytes=header.next_zstd_dictionary_length_bytes,
        conf_block_length_bytes=header.conf_block_length_bytes,
        check_visibility=header.check_visibility,
        configuration_entries=configuration_entries_to_mapping(database.read_configuration_block()),
    )
