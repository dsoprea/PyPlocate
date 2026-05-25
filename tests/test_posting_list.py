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
