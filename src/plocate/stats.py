"""Database statistics collection."""

import dataclasses
import typing

import plocate.config



@dataclasses.dataclass(frozen=True, slots=True)
class DatabaseStatistics:
    """Summary metrics collected from a plocate database."""

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
        """Return a JSON-serializable mapping of these statistics."""

        mapping = dataclasses.asdict(self)

        return mapping


class _StatisticsSource(typing.Protocol):
    """Minimal database surface needed to collect statistics."""

    path: str | None
    file_size: int
    header: object

    def filename_block_offsets(self) -> tuple[int, ...]: ...
    def iter_filename_blocks(self): ...
    def read_configuration_block(self): ...


def _compressed_filename_byte_count(offsets: tuple[int, ...], docid_count: int) -> int:
    """Return the total compressed filename bytes spanned by offsets."""

    if docid_count == 0:
        return 0

    byte_count = offsets[-1] - offsets[0]

    return byte_count


def _count_paths(database: _StatisticsSource) -> int:
    """Count every indexed path by walking filename blocks."""

    total = 0
    blocks = database.iter_filename_blocks()
    for block_paths in blocks:
        total += len(block_paths)

    return total


def collect_statistics(database: _StatisticsSource) -> DatabaseStatistics:
    """Collect summary statistics from an open plocate database."""

    offsets = database.filename_block_offsets()
    header = database.header
    path_count = _count_paths(database)
    configuration_block = database.read_configuration_block()
    configuration_entries = plocate.config.configuration_entries_to_mapping(configuration_block)
    compressed_bytes = _compressed_filename_byte_count(offsets, header.num_docids)

    return DatabaseStatistics(
        database_path=database.path,
        file_size_bytes=database.file_size,
        version=header.version,
        max_version=header.max_version,
        num_docids=header.num_docids,
        path_count=path_count,
        hashtable_size=header.hashtable_size,
        extra_ht_slots=header.extra_ht_slots,
        hash_table_offset_bytes=header.hash_table_offset_bytes,
        filename_index_offset_bytes=header.filename_index_offset_bytes,
        compressed_filename_bytes=compressed_bytes,
        zstd_dictionary_length_bytes=header.zstd_dictionary_length_bytes,
        directory_data_length_bytes=header.directory_data_length_bytes,
        next_zstd_dictionary_length_bytes=header.next_zstd_dictionary_length_bytes,
        conf_block_length_bytes=header.conf_block_length_bytes,
        check_visibility=header.check_visibility,
        configuration_entries=configuration_entries,
    )
