"""Tests for plocate.binary_reader."""

import io

import pytest

import plocate.binary_reader
import plocate.errors



def test_binary_reader_reads_from_memory():
    """Read byte ranges from an in-memory file object."""

    payload = b"abcdefgh"
    reader = plocate.binary_reader.BinaryReader(io.BytesIO(payload))
    assert reader.file_size == len(payload)
    assert reader.read_bytes(2, 3) == b"cde"
    reader.close()


def test_binary_reader_raises_on_short_read():
    """Raise PlocateFormatError when a read extends past EOF."""

    reader = plocate.binary_reader.BinaryReader(io.BytesIO(b"abc"))
    with pytest.raises(plocate.errors.PlocateFormatError, match="unexpected end of file"):
        reader.read_bytes(1, 5)
    reader.close()
