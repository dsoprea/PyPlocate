"""Filename index and compressed block decoding."""

import zstandard

import plocate.errors



def read_filename_block_offsets(index_bytes: bytes, expected_docid_count: int) -> tuple[int, ...]:
    """Parse the uint64 filename block offset table."""

    entry_count = expected_docid_count + 1
    expected_length = entry_count * 8
    if len(index_bytes) != expected_length:
        message = "filename index has {actual_length} bytes, expected {expected_length}".format(
            actual_length=len(index_bytes),
            expected_length=expected_length,
        )
        raise plocate.errors.PlocateFormatError(message)

    index_range = range(0, len(index_bytes), 8)
    offsets = tuple(
        int.from_bytes(index_bytes[index : index + 8], "little")
        for index in index_range
    )

    return offsets


def parse_null_terminated_paths(block_bytes: bytes) -> list[str]:
    """Split a decompressed block into UTF-8 path strings."""

    if not block_bytes.endswith(b"\0"):
        block_bytes += b"\0"

    paths: list[str] = []
    start_index = 0

    # Each path is a NUL-terminated string; empty strings are skipped.
    while start_index < len(block_bytes):
        end_index = block_bytes.find(b"\0", start_index)
        if end_index == -1:
            break
        if end_index > start_index:
            path_bytes = block_bytes[start_index:end_index]
            paths.append(path_bytes.decode("utf-8", errors="surrogateescape"))
        start_index = end_index + 1

    return paths


def decompress_filename_block(
    compressed: bytes,
    decompressor: zstandard.ZstdDecompressor,
) -> list[str]:
    """Decompress one zstd filename block and parse its paths."""

    decompressed = decompressor.decompress(compressed)
    paths = parse_null_terminated_paths(decompressed)

    return paths


def build_zstd_decompressor(dictionary_bytes: bytes | None) -> zstandard.ZstdDecompressor:
    """Build a decompressor, optionally trained on the database dictionary."""

    if dictionary_bytes:
        dictionary = zstandard.ZstdCompressionDict(dictionary_bytes)
        decompressor = zstandard.ZstdDecompressor(dict_data=dictionary)

        return decompressor

    return zstandard.ZstdDecompressor()
