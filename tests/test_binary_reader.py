import io

import pytest

from plocate_db.binary_reader import BinaryReader
from plocate_db.errors import PlocateFormatError


def test_binary_reader_reads_from_memory():
    payload = b"abcdefgh"
    reader = BinaryReader(io.BytesIO(payload))
    assert reader.file_size == len(payload)
    assert reader.read_bytes(2, 3) == b"cde"
    reader.close()


def test_binary_reader_raises_on_short_read():
    reader = BinaryReader(io.BytesIO(b"abc"))
    with pytest.raises(PlocateFormatError, match="unexpected end of file"):
        reader.read_bytes(1, 5)
    reader.close()
