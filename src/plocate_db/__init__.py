"""Read and search plocate.db index files."""

from plocate_db.binary_reader import BinaryReader
from plocate_db.config import ConfigurationEntry, configuration_entries_to_mapping, parse_configuration_block
from plocate_db.constants import DEFAULT_DATABASE_PATH
from plocate_db.database import PlocateDatabase
from plocate_db.errors import PlocateDatabaseError, PlocateFormatError
from plocate_db.filename_index import (
    build_zstd_decompressor,
    decompress_filename_block,
    parse_null_terminated_paths,
    read_filename_block_offsets,
)
from plocate_db.formatting import format_bytes, format_search_matches, format_statistics_text
from plocate_db.header import HEADER_STRUCT, PLOCATE_MAGIC, PlocateHeader
from plocate_db.patterns import CompiledPattern, PatternKind, compile_pattern, matches_all_patterns, matches_pattern
from plocate_db.search import SearchOptions, search_database, search_paths
from plocate_db.stats import DatabaseStatistics, collect_statistics, compressed_filename_byte_count, count_paths

__all__ = [
    "BinaryReader",
    "CompiledPattern",
    "ConfigurationEntry",
    "DEFAULT_DATABASE_PATH",
    "DatabaseStatistics",
    "HEADER_STRUCT",
    "PLOCATE_MAGIC",
    "PatternKind",
    "PlocateDatabase",
    "PlocateDatabaseError",
    "PlocateFormatError",
    "PlocateHeader",
    "SearchOptions",
    "build_zstd_decompressor",
    "collect_statistics",
    "compile_pattern",
    "compressed_filename_byte_count",
    "configuration_entries_to_mapping",
    "count_paths",
    "decompress_filename_block",
    "format_bytes",
    "format_search_matches",
    "format_statistics_text",
    "matches_all_patterns",
    "matches_pattern",
    "parse_configuration_block",
    "parse_null_terminated_paths",
    "read_filename_block_offsets",
    "search_database",
    "search_paths",
]
