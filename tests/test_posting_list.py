"""Tests for plocate.posting_list."""

import logging

import plocate.posting_list

import tests.support.index_builder

_LOGGER = logging.getLogger(__name__)


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


def test_search_real_database_posting_lists():
    """Decode posting lists from a real updatedb fixture database."""

    import os

    import plocate.database
    import plocate.search

    database_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "asset",
        "test",
        "test.db",
    )
    if not os.path.isfile(database_path):
        return

    pattern = "test_stats.cpython-314-pytest-9.0.3.pyc"
    with plocate.database.PlocateDatabase.open(database_path) as database:
        match_iterator = plocate.search.search_database(database, pattern)
        matches = list(match_iterator)
    assert len(matches) >= 1
    assert any(pattern in match for match in matches)
