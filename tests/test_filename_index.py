"""Tests for plocate.filename_index."""

import logging
import struct

import pytest
import zstandard

import plocate.errors
import plocate.filename_index
import tests.support.fixture_builder

_LOGGER = logging.getLogger(__name__)


def test_encode_paths_block():
    """Encode paths as a trailing-NUL block."""

    encoded = tests.support.fixture_builder.encode_paths_block(["/a", "/b"])
    assert encoded == b"/a\0/b\0"


def test_parse_null_terminated_paths():
    """Split a decompressed block into individual path strings."""

    paths = plocate.filename_index.parse_null_terminated_paths(b"/a\0/b\0\0")
    assert paths == ["/a", "/b"]


def test_read_filename_block_offsets():
    """Parse uint64 filename block offsets from index bytes."""

    index_bytes = struct.pack("<QQQ", 100, 200, 300)
    offsets = plocate.filename_index.read_filename_block_offsets(index_bytes, 2)
    assert offsets == (100, 200, 300)


def test_read_filename_block_offsets_rejects_bad_length():
    """Reject index bytes whose length does not match the docid count."""

    with pytest.raises(plocate.errors.PlocateFormatError, match="filename index"):
        plocate.filename_index.read_filename_block_offsets(b"\00" * 7, 2)


def test_decompress_fixture_block():
    """Decompress a zstd path block built by the test fixture helper."""

    compressed = tests.support.fixture_builder.compress_paths_block(["/one", "/two"])
    decompressor = zstandard.ZstdDecompressor()
    paths = plocate.filename_index.decompress_filename_block(compressed, decompressor)
    assert paths == ["/one", "/two"]
