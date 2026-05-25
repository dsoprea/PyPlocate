"""Human-readable and JSON output formatting."""

import logging

import plocate.stats

_LOGGER = logging.getLogger(__name__)


def _format_bytes(num_bytes: int) -> str:
    """Format a byte count using B, KiB, MiB, or GiB units."""

    if num_bytes < 1024:
        formatted = "{num_bytes} B".format(num_bytes=num_bytes)

        return formatted
    if num_bytes < 1024 * 1024:
        kibibytes = num_bytes / 1024
        formatted = "{kibibytes:.1f} KiB".format(kibibytes=kibibytes)

        return formatted
    if num_bytes < 1024 * 1024 * 1024:
        mebibytes = num_bytes / (1024 * 1024)
        formatted = "{mebibytes:.1f} MiB".format(mebibytes=mebibytes)

        return formatted

    gibibytes = num_bytes / (1024 * 1024 * 1024)
    formatted = "{gibibytes:.2f} GiB".format(gibibytes=gibibytes)

    return formatted


def format_statistics_text(statistics: plocate.stats.DatabaseStatistics) -> str:
    """Render database statistics as human-readable text."""

    lines = [
        "database: {database_path}".format(database_path=statistics.database_path),
        "file size: {file_size}".format(file_size=_format_bytes(statistics.file_size_bytes)),
        "version: {version}".format(version=statistics.version),
        "max version: {max_version}".format(max_version=statistics.max_version),
        "filename blocks: {num_docids}".format(num_docids=statistics.num_docids),
        "indexed paths: {path_count}".format(path_count=statistics.path_count),
        "hashtable size: {hashtable_size}".format(hashtable_size=statistics.hashtable_size),
        "extra hashtable slots: {extra_ht_slots}".format(extra_ht_slots=statistics.extra_ht_slots),
        "hash table offset: {hash_table_offset_bytes}".format(
            hash_table_offset_bytes=statistics.hash_table_offset_bytes,
        ),
        "filename index offset: {filename_index_offset_bytes}".format(
            filename_index_offset_bytes=statistics.filename_index_offset_bytes,
        ),
        "compressed filename bytes: {compressed_filename_bytes}".format(
            compressed_filename_bytes=_format_bytes(statistics.compressed_filename_bytes),
        ),
        "zstd dictionary bytes: {zstd_dictionary_length_bytes}".format(
            zstd_dictionary_length_bytes=_format_bytes(statistics.zstd_dictionary_length_bytes),
        ),
        "directory data bytes: {directory_data_length_bytes}".format(
            directory_data_length_bytes=_format_bytes(statistics.directory_data_length_bytes),
        ),
        "next zstd dictionary bytes: {next_zstd_dictionary_length_bytes}".format(
            next_zstd_dictionary_length_bytes=_format_bytes(statistics.next_zstd_dictionary_length_bytes),
        ),
        "configuration block bytes: {conf_block_length_bytes}".format(
            conf_block_length_bytes=_format_bytes(statistics.conf_block_length_bytes),
        ),
        "check visibility: {check_visibility}".format(check_visibility=statistics.check_visibility),
    ]

    if statistics.configuration_entries:
        lines.append("configuration:")
        sorted_entries = sorted(statistics.configuration_entries.items())
        for name, values in sorted_entries:
            value_text = ", ".join(values)
            line = "  {name}: {value_text}".format(name=name, value_text=value_text)
            lines.append(line)

    text = "\n".join(lines)

    return text


def format_search_matches(matches: list[str], *, use_null_separator: bool) -> str:
    """Format search matches for stdout using newline or NUL separators."""

    if not matches:
        return ""
    if use_null_separator:
        formatted = "\0".join(matches) + "\0"

        return formatted

    formatted = "\n".join(matches) + "\n"

    return formatted
