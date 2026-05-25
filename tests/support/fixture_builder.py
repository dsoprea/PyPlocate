"""Build minimal plocate.db files for tests."""

import logging
import struct

import zstandard

import plocate.directory_data
import plocate.header

_LOGGER = logging.getLogger(__name__)


def encode_paths_block(paths: list[str]) -> bytes:
    """Encode paths as a NUL-delimited UTF-8 block."""

    parts = [path.encode("utf-8") for path in paths]
    encoded = b"\0".join(parts) + b"\0"

    return encoded


def compress_paths_block(paths: list[str]) -> bytes:
    """Compress a NUL-delimited path block with zstd."""

    compressor = zstandard.ZstdCompressor()
    encoded = encode_paths_block(paths)
    compressed = compressor.compress(encoded)

    return compressed


def build_configuration_block(entries: dict[str, list[str]]) -> bytes:
    """Build a plocate configuration block from name-to-values mappings."""

    block = bytearray()
    sorted_names = sorted(entries)
    for name in sorted_names:
        block.extend(name.encode("utf-8"))
        block.append(0)
        for value in entries[name]:
            block.extend(value.encode("utf-8"))
            block.append(0)
        block.append(0)

    return bytes(block)


def build_minimal_database_bytes(
    paths: list[str],
    *,
    configuration_entries: dict[str, list[str]] | None = None,
    check_visibility: bool = False,
    directory_time_entries: list[plocate.directory_data.DirectoryTimeEntry] | None = None,
) -> bytes:
    """Build a minimal valid plocate.db file containing the given paths."""

    if directory_time_entries is not None and len(directory_time_entries) != len(paths):
        message = "directory_time_entries length {entry_count} does not match paths length {path_count}".format(
            entry_count=len(directory_time_entries),
            path_count=len(paths),
        )
        raise ValueError(message)

    # Compress the filename block and lay out index offsets.
    compressed_block = compress_paths_block(paths)
    data_offset = plocate.header.HEADER_STRUCT.size
    index_offset = data_offset + len(compressed_block)
    index_bytes = struct.pack("<QQ", data_offset, index_offset)

    # Append optional directory timestamp and configuration blocks after the index.
    directory_data = b""
    directory_data_offset = 0
    if directory_time_entries is not None:
        directory_block = plocate.directory_data.encode_directory_time_block(directory_time_entries)
        directory_data = plocate.directory_data.compress_directory_time_block(directory_block)
        directory_data_offset = index_offset + len(index_bytes)

    conf_block = b""
    conf_offset = 0
    if configuration_entries is not None:
        conf_block = build_configuration_block(configuration_entries)
        if directory_data:
            conf_offset = directory_data_offset + len(directory_data)
        else:
            conf_offset = index_offset + len(index_bytes)

    if directory_data:
        hash_table_offset = conf_offset + len(conf_block)
    elif conf_block:
        hash_table_offset = conf_offset + len(conf_block)
    else:
        hash_table_offset = index_offset + len(index_bytes)

    if configuration_entries is not None or directory_time_entries is not None:
        max_version = 2
    else:
        max_version = 1

    # Serialize the header and concatenate database sections.
    header = plocate.header.PlocateHeader(
        magic=plocate.header.PLOCATE_MAGIC,
        version=1,
        hashtable_size=1,
        extra_ht_slots=16,
        num_docids=1,
        hash_table_offset_bytes=hash_table_offset,
        filename_index_offset_bytes=index_offset,
        max_version=max_version,
        zstd_dictionary_length_bytes=0,
        zstd_dictionary_offset_bytes=plocate.header.HEADER_STRUCT.size,
        directory_data_length_bytes=len(directory_data),
        directory_data_offset_bytes=directory_data_offset,
        next_zstd_dictionary_length_bytes=0,
        next_zstd_dictionary_offset_bytes=0,
        conf_block_length_bytes=len(conf_block),
        conf_block_offset_bytes=conf_offset,
        check_visibility=check_visibility,
    )

    database_bytes = bytearray()
    database_bytes.extend(header.to_bytes())
    database_bytes.extend(compressed_block)
    database_bytes.extend(index_bytes)
    if directory_data:
        database_bytes.extend(directory_data)
    if conf_block:
        database_bytes.extend(conf_block)

    return bytes(database_bytes)
