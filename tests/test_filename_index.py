import struct

import pytest

from plocate_db.errors import PlocateFormatError
from plocate_db.filename_index import (
    parse_null_terminated_paths,
    read_filename_block_offsets,
)
from tests.support.fixture_builder import compress_paths_block, encode_paths_block


def test_encode_paths_block():
    assert encode_paths_block(["/a", "/b"]) == b"/a\0/b\0"


def test_parse_null_terminated_paths():
    paths = parse_null_terminated_paths(b"/a\0/b\0\0")
    assert paths == ["/a", "/b"]


def test_read_filename_block_offsets():
    index_bytes = struct.pack("<QQQ", 100, 200, 300)
    assert read_filename_block_offsets(index_bytes, 2) == (100, 200, 300)


def test_read_filename_block_offsets_rejects_bad_length():
    with pytest.raises(PlocateFormatError, match="filename index"):
        read_filename_block_offsets(b"\00" * 7, 2)


def test_decompress_fixture_block():
    from plocate_db.filename_index import decompress_filename_block

    compressed = compress_paths_block(["/one", "/two"])
    paths = decompress_filename_block(compressed, __import__("zstandard").ZstdDecompressor())
    assert paths == ["/one", "/two"]
