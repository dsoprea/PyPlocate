"""Tests for plocate.formatting."""

import logging

import plocate.formatting
import plocate.stats

_LOGGER = logging.getLogger(__name__)


def test_format_bytes():
    """Format byte counts using B, KiB, and MiB units."""

    assert plocate.formatting._format_bytes(512) == "512 B"
    assert plocate.formatting._format_bytes(2048) == "2.0 KiB"
    assert plocate.formatting._format_bytes(5 * 1024 * 1024) == "5.0 MiB"


def test_format_statistics_text():
    """Render database statistics as human-readable text."""

    statistics = plocate.stats.DatabaseStatistics(
        database_path="test.db",
        file_size_bytes=2048,
        version=1,
        max_version=2,
        num_docids=1,
        path_count=3,
        hashtable_size=1,
        extra_ht_slots=16,
        hash_table_offset_bytes=300,
        filename_index_offset_bytes=200,
        compressed_filename_bytes=100,
        zstd_dictionary_length_bytes=0,
        directory_data_length_bytes=0,
        next_zstd_dictionary_length_bytes=0,
        conf_block_length_bytes=10,
        check_visibility=False,
        configuration_entries={"prune_bind_mounts": ["0"]},
    )

    text = plocate.formatting.format_statistics_text(statistics)
    assert "database: test.db" in text
    assert "indexed paths: 3" in text
    assert "prune_bind_mounts: 0" in text


def test_format_search_matches():
    """Format search matches with newline or NUL separators."""

    assert plocate.formatting.format_search_matches(["/a", "/b"], use_null_separator=False) == "/a\n/b\n"
    assert plocate.formatting.format_search_matches(["/a"], use_null_separator=True) == "/a\0"
    assert plocate.formatting.format_search_matches([], use_null_separator=False) == ""
