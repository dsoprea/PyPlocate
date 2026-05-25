"""Tests for plocate.config."""

import logging

import plocate.config

_LOGGER = logging.getLogger(__name__)


def test_parse_configuration_block():
    """Parse NUL-delimited configuration entries from a block."""

    block = b"prune_bind_mounts\0" + b"0\0\0" + b"prunepaths\0/tmp\0/var/cache\0\0"
    entries = plocate.config.parse_configuration_block(block)

    assert len(entries) == 2
    assert entries[0].name == "prune_bind_mounts"
    assert entries[0].values == ["0"]
    assert entries[1].name == "prunepaths"
    assert entries[1].values == ["/tmp", "/var/cache"]


def test_configuration_entries_to_mapping():
    """Convert parsed configuration entries to a name-to-values mapping."""

    block = b"prunefs\009P\0NFS\0\0"
    parsed_entries = plocate.config.parse_configuration_block(block)
    mapping = plocate.config.configuration_entries_to_mapping(parsed_entries)
    assert mapping == {"prunefs": ["9P", "NFS"]}
