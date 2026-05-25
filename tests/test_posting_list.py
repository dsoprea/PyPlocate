"""Tests for plocate.posting_list."""

import plocate.posting_list

import tests.support.index_builder



def test_decode_single_docid_posting_list():
    """Decode a posting list containing one docid."""

    encoded = tests.support.index_builder.write_baseval(0)
    docids = plocate.posting_list.decode_posting_list_docids(encoded, 1)
    assert docids == (0,)


def test_decode_constant_posting_list_with_decode_slop():
    """Decode a compact constant block that reads past the encoded length."""

    encoded = bytes([0x00, 0xC0])
    decode_buffer = encoded + (b"\x00" * plocate.posting_list.POSTING_LIST_DECODE_SLOP_BYTES)
    docids = plocate.posting_list.decode_posting_list_docids(decode_buffer, 4)
    assert docids == (0, 1, 2, 3)
