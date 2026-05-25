"""Filename index and compressed block decoding."""

from __future__ import annotations

import zstandard

from plocate_db.errors import PlocateFormatError


def read_filename_block_offsets(index_bytes: bytes, expected_docid_count: int) -> tuple[int, ...]:
    entry_count = expected_docid_count + 1
    expected_length = entry_count * 8
    if len(index_bytes) != expected_length:
        raise PlocateFormatError(
            f"filename index has {len(index_bytes)} bytes, expected {expected_length}"
        )

    offsets = tuple(
        int.from_bytes(index_bytes[index : index + 8], "little")
        for index in range(0, len(index_bytes), 8)
    )
    return offsets


def parse_null_terminated_paths(block_bytes: bytes) -> list[str]:
    if not block_bytes.endswith(b"\0"):
        block_bytes += b"\0"

    paths: list[str] = []
    start_index = 0
    while start_index < len(block_bytes):
        end_index = block_bytes.find(b"\0", start_index)
        if end_index == -1:
            break
        if end_index > start_index:
            paths.append(block_bytes[start_index:end_index].decode("utf-8", errors="surrogateescape"))
        start_index = end_index + 1

    return paths


def decompress_filename_block(
    compressed: bytes,
    decompressor: zstandard.ZstdDecompressor,
) -> list[str]:
    decompressed = decompressor.decompress(compressed)
    return parse_null_terminated_paths(decompressed)


def build_zstd_decompressor(dictionary_bytes: bytes | None) -> zstandard.ZstdDecompressor:
    if dictionary_bytes:
        dictionary = zstandard.ZstdCompressionDict(dictionary_bytes)
        return zstandard.ZstdDecompressor(dict_data=dictionary)
    return zstandard.ZstdDecompressor()
