"""Directory timestamp stream parsing for plocate databases."""

import collections.abc
import dataclasses
import io
import logging
import struct

import zstandard

import plocate.errors

_LOGGER = logging.getLogger(__name__)

DIRECTORY_TIME_FILE_MARKER = 0
DIRECTORY_TIME_DIRECTORY_MARKER = 1
DIRECTORY_TIME_DIRECTORY_BODY_STRUCT = struct.Struct("<qi")


@dataclasses.dataclass(frozen=True, slots=True)
class DirectoryTimeEntry:
    """Directory timestamp metadata aligned with one indexed path."""

    is_directory: bool
    seconds: int | None = None
    nanoseconds: int | None = None


def _encode_directory_time_entry(entry: DirectoryTimeEntry) -> bytes:
    """Encode one directory timestamp entry for tests and fixtures."""

    if not entry.is_directory:
        encoded = bytes([DIRECTORY_TIME_FILE_MARKER])

        return encoded
    if entry.seconds is None or entry.nanoseconds is None:
        message = "directory entries require seconds and nanoseconds"
        raise ValueError(message)

    encoded = bytes([DIRECTORY_TIME_DIRECTORY_MARKER])
    encoded += DIRECTORY_TIME_DIRECTORY_BODY_STRUCT.pack(entry.seconds, entry.nanoseconds)

    return encoded


def _encode_directory_time_block(entries: collections.abc.Sequence[DirectoryTimeEntry]) -> bytes:
    """Encode a directory timestamp block from ordered entries."""

    block_parts: list[bytes] = []
    for entry in entries:
        encoded_entry = _encode_directory_time_entry(entry)
        block_parts.append(encoded_entry)
    block = b"".join(block_parts)

    return block


def _compress_directory_time_block(block_bytes: bytes) -> bytes:
    """Compress a directory timestamp block using a zstd stream."""

    compressor = zstandard.ZstdCompressor()
    buffer = io.BytesIO()
    stream_writer = compressor.stream_writer(buffer)
    stream_writer.write(block_bytes)
    stream_writer.flush(zstandard.FLUSH_FRAME)
    compressed = buffer.getvalue()
    stream_writer.close()

    return compressed


def decompress_directory_data_bytes(compressed: bytes) -> bytes:
    """Decompress a zstd directory timestamp stream."""

    decompressor = zstandard.ZstdDecompressor()
    buffer = io.BytesIO(compressed)
    stream_reader = decompressor.stream_reader(buffer)
    decompressed = stream_reader.read()
    stream_reader.close()

    return decompressed


def parse_directory_time_entries(
    block_bytes: bytes,
) -> tuple[DirectoryTimeEntry, ...]:
    """Parse decompressed directory timestamp bytes into ordered entries."""

    entries: list[DirectoryTimeEntry] = []
    index = 0

    # Each entry begins with a marker byte for file versus directory.
    while index < len(block_bytes):
        marker = block_bytes[index]
        index += 1
        if marker == DIRECTORY_TIME_FILE_MARKER:
            entry = DirectoryTimeEntry(is_directory=False)
            entries.append(entry)
            continue
        if marker == DIRECTORY_TIME_DIRECTORY_MARKER:
            if index + DIRECTORY_TIME_DIRECTORY_BODY_STRUCT.size > len(block_bytes):
                message = "truncated directory timestamp entry at byte {index}".format(index=index - 1)
                raise plocate.errors.PlocateFormatError(message)
            seconds, nanoseconds = DIRECTORY_TIME_DIRECTORY_BODY_STRUCT.unpack_from(block_bytes, index)
            index += DIRECTORY_TIME_DIRECTORY_BODY_STRUCT.size
            entry = DirectoryTimeEntry(
                is_directory=True,
                seconds=seconds,
                nanoseconds=nanoseconds,
            )
            entries.append(entry)
            continue

        message = "unsupported directory timestamp marker {marker}".format(marker=marker)
        raise plocate.errors.PlocateFormatError(message)

    return tuple(entries)
