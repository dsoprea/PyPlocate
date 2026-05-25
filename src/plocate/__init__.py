"""Read and search plocate.db index files."""

import logging

import plocate.binary_reader
import plocate.config
import plocate.constants
import plocate.database
import plocate.errors
import plocate.filename_index
import plocate.formatting
import plocate.header
import plocate.patterns
import plocate.search
import plocate.stats

_LOGGER = logging.getLogger(__name__)

BinaryReader = plocate.binary_reader.BinaryReader
CompiledPattern = plocate.patterns.CompiledPattern
ConfigurationEntry = plocate.config.ConfigurationEntry
DEFAULT_DATABASE_PATH = plocate.constants.DEFAULT_DATABASE_PATH
DatabaseStatistics = plocate.stats.DatabaseStatistics
HEADER_STRUCT = plocate.header.HEADER_STRUCT
PLOCATE_MAGIC = plocate.header.PLOCATE_MAGIC
PatternKind = plocate.patterns.PatternKind
PlocateDatabase = plocate.database.PlocateDatabase
PlocateDatabaseError = plocate.errors.PlocateDatabaseError
PlocateFormatError = plocate.errors.PlocateFormatError
PlocateHeader = plocate.header.PlocateHeader
SearchOptions = plocate.search.SearchOptions
build_zstd_decompressor = plocate.filename_index.build_zstd_decompressor
collect_statistics = plocate.stats.collect_statistics
compile_pattern = plocate.patterns.compile_pattern
compressed_filename_byte_count = plocate.stats.compressed_filename_byte_count
configuration_entries_to_mapping = plocate.config.configuration_entries_to_mapping
count_paths = plocate.stats.count_paths
decompress_filename_block = plocate.filename_index.decompress_filename_block
format_bytes = plocate.formatting.format_bytes
format_search_matches = plocate.formatting.format_search_matches
format_statistics_text = plocate.formatting.format_statistics_text
matches_all_patterns = plocate.patterns.matches_all_patterns
matches_pattern = plocate.patterns.matches_pattern
parse_configuration_block = plocate.config.parse_configuration_block
parse_null_terminated_paths = plocate.filename_index.parse_null_terminated_paths
read_filename_block_offsets = plocate.filename_index.read_filename_block_offsets
search_database = plocate.search.search_database
search_paths = plocate.search.search_paths

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
