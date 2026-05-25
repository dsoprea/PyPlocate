"""Tests for plocate.directory_data."""

import logging

import plocate.directory_data

_LOGGER = logging.getLogger(__name__)


def test_encode_and_parse_directory_time_block():
    """Round-trip directory timestamp entries through compression."""

    entries = [
        plocate.directory_data.DirectoryTimeEntry(
            is_directory=True,
            seconds=1700000000,
            nanoseconds=123456789,
        ),
        plocate.directory_data.DirectoryTimeEntry(is_directory=False),
    ]
    block_bytes = plocate.directory_data.encode_directory_time_block(entries)
    compressed = plocate.directory_data.compress_directory_time_block(block_bytes)
    decompressed = plocate.directory_data.decompress_directory_data_bytes(compressed)
    parsed_entries = plocate.directory_data.parse_directory_time_entries(decompressed)
    assert parsed_entries == tuple(entries)
