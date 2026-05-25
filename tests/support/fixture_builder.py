"""Build minimal plocate.db files for tests."""

from __future__ import annotations

import struct

import zstandard

from plocate_db.header import HEADER_STRUCT, PLOCATE_MAGIC, PlocateHeader


def encode_paths_block(paths: list[str]) -> bytes:
    parts = [path.encode("utf-8") for path in paths]
    return b"\0".join(parts) + b"\0"


def compress_paths_block(paths: list[str]) -> bytes:
    compressor = zstandard.ZstdCompressor()
    return compressor.compress(encode_paths_block(paths))


def build_configuration_block(entries: dict[str, list[str]]) -> bytes:
    block = bytearray()
    for name in sorted(entries):
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
) -> bytes:
    compressed_block = compress_paths_block(paths)
    data_offset = HEADER_STRUCT.size
    index_offset = data_offset + len(compressed_block)
    index_bytes = struct.pack("<QQ", data_offset, index_offset)

    conf_block = b""
    conf_offset = 0
    if configuration_entries is not None:
        conf_block = build_configuration_block(configuration_entries)
        conf_offset = index_offset + len(index_bytes)

    hash_table_offset = conf_offset + len(conf_block)

    header = PlocateHeader(
        magic=PLOCATE_MAGIC,
        version=1,
        hashtable_size=1,
        extra_ht_slots=16,
        num_docids=1,
        hash_table_offset_bytes=hash_table_offset,
        filename_index_offset_bytes=index_offset,
        max_version=2 if configuration_entries is not None else 1,
        zstd_dictionary_length_bytes=0,
        zstd_dictionary_offset_bytes=HEADER_STRUCT.size,
        directory_data_length_bytes=0,
        directory_data_offset_bytes=0,
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
    if conf_block:
        database_bytes.extend(conf_block)
    return bytes(database_bytes)
