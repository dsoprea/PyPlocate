"""Tests for plocate.header."""

import logging
import struct

import pytest

import plocate.header

_LOGGER = logging.getLogger(__name__)


def test_header_round_trip():
    """Serialize and parse a header without losing field values."""

    header = plocate.header.PlocateHeader(
        magic=plocate.header.PLOCATE_MAGIC,
        version=1,
        hashtable_size=10,
        extra_ht_slots=16,
        num_docids=3,
        hash_table_offset_bytes=500,
        filename_index_offset_bytes=400,
        max_version=2,
        zstd_dictionary_length_bytes=0,
        zstd_dictionary_offset_bytes=112,
        directory_data_length_bytes=0,
        directory_data_offset_bytes=0,
        next_zstd_dictionary_length_bytes=0,
        next_zstd_dictionary_offset_bytes=0,
        conf_block_length_bytes=0,
        conf_block_offset_bytes=0,
        check_visibility=True,
    )

    header_bytes = header.to_bytes()
    parsed = plocate.header.PlocateHeader.from_bytes(header_bytes)
    assert parsed == header


def test_header_rejects_invalid_magic():
    """Reject headers whose magic bytes are not \\0plocate."""

    header_bytes = bytearray(plocate.header.HEADER_STRUCT.size)
    header_bytes[:8] = b"invalid!"

    with pytest.raises(ValueError, match="magic number"):
        plocate.header.PlocateHeader.from_bytes(bytes(header_bytes))


def test_header_rejects_unsupported_version():
    """Reject headers whose version field is not 0 or 1."""

    header = plocate.header.PlocateHeader(
        magic=plocate.header.PLOCATE_MAGIC,
        version=9,
        hashtable_size=1,
        extra_ht_slots=16,
        num_docids=1,
        hash_table_offset_bytes=200,
        filename_index_offset_bytes=150,
        max_version=1,
        zstd_dictionary_length_bytes=0,
        zstd_dictionary_offset_bytes=112,
        directory_data_length_bytes=0,
        directory_data_offset_bytes=0,
        next_zstd_dictionary_length_bytes=0,
        next_zstd_dictionary_offset_bytes=0,
        conf_block_length_bytes=0,
        conf_block_offset_bytes=0,
        check_visibility=False,
    )

    with pytest.raises(ValueError, match="unsupported database version"):
        plocate.header.PlocateHeader.from_bytes(header.to_bytes())


def test_header_struct_size():
    """Confirm the header struct size matches the C layout."""

    assert plocate.header.HEADER_STRUCT.size == 112
    assert struct.calcsize("<8s4I2Q2IQ6Q?7x") == 112
