"""Human-readable and JSON output formatting."""

from __future__ import annotations

from plocate_db.stats import DatabaseStatistics


def format_bytes(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KiB"
    if num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MiB"
    return f"{num_bytes / (1024 * 1024 * 1024):.2f} GiB"


def format_statistics_text(statistics: DatabaseStatistics) -> str:
    lines = [
        f"database: {statistics.database_path}",
        f"file size: {format_bytes(statistics.file_size_bytes)}",
        f"version: {statistics.version}",
        f"max version: {statistics.max_version}",
        f"filename blocks: {statistics.num_docids}",
        f"indexed paths: {statistics.path_count}",
        f"hashtable size: {statistics.hashtable_size}",
        f"extra hashtable slots: {statistics.extra_ht_slots}",
        f"hash table offset: {statistics.hash_table_offset_bytes}",
        f"filename index offset: {statistics.filename_index_offset_bytes}",
        f"compressed filename bytes: {format_bytes(statistics.compressed_filename_bytes)}",
        f"zstd dictionary bytes: {format_bytes(statistics.zstd_dictionary_length_bytes)}",
        f"directory data bytes: {format_bytes(statistics.directory_data_length_bytes)}",
        f"next zstd dictionary bytes: {format_bytes(statistics.next_zstd_dictionary_length_bytes)}",
        f"configuration block bytes: {format_bytes(statistics.conf_block_length_bytes)}",
        f"check visibility: {statistics.check_visibility}",
    ]

    if statistics.configuration_entries:
        lines.append("configuration:")
        for name, values in sorted(statistics.configuration_entries.items()):
            lines.append(f"  {name}: {', '.join(values)}")

    return "\n".join(lines)


def format_search_matches(matches: list[str], *, use_null_separator: bool) -> str:
    if not matches:
        return ""
    if use_null_separator:
        return "\0".join(matches) + "\0"
    return "\n".join(matches) + "\n"
