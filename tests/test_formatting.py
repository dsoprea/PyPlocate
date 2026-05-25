from plocate_db.formatting import format_bytes, format_search_matches, format_statistics_text
from plocate_db.stats import DatabaseStatistics


def test_format_bytes():
    assert format_bytes(512) == "512 B"
    assert format_bytes(2048) == "2.0 KiB"
    assert format_bytes(5 * 1024 * 1024) == "5.0 MiB"


def test_format_statistics_text():
    statistics = DatabaseStatistics(
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

    text = format_statistics_text(statistics)
    assert "database: test.db" in text
    assert "indexed paths: 3" in text
    assert "prune_bind_mounts: 0" in text


def test_format_search_matches():
    assert format_search_matches(["/a", "/b"], use_null_separator=False) == "/a\n/b\n"
    assert format_search_matches(["/a"], use_null_separator=True) == "/a\0"
    assert format_search_matches([], use_null_separator=False) == ""
