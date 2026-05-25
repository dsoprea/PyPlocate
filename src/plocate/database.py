"""Core plocate.db reader."""

import collections.abc
import logging
import typing

import zstandard

import plocate.binary_reader
import plocate.config
import plocate.directory_data
import plocate.errors
import plocate.filename_index
import plocate.header
import plocate.indexed_entry
import plocate.stats
import plocate.trigram_index

_LOGGER = logging.getLogger(__name__)


class PlocateDatabase:
    """Reader for a plocate.db index file."""

    def __init__(self, file_object: typing.BinaryIO, *, path: str | None = None) -> None:
        """Open a plocate database from a readable binary file object."""

        self._reader = plocate.binary_reader.BinaryReader(file_object)
        self._path = path
        self._decompressor: zstandard.ZstdDecompressor | None = None
        self._filename_offsets: tuple[int, ...] | None = None
        self._directory_time_entries: tuple[plocate.directory_data.DirectoryTimeEntry, ...] | None = None
        self._directory_time_entries_loaded = False
        self._trigram_index: plocate.trigram_index.TrigramIndex | None = None
        self._trigram_index_loaded = False

        # Parse the fixed header and prepare decompression.
        header_bytes = self._reader.read_bytes(0, plocate.header.HEADER_STRUCT.size)
        try:
            self.header = plocate.header.PlocateHeader.from_bytes(header_bytes)
        except ValueError as error:
            raise plocate.errors.PlocateFormatError(str(error)) from error

        dictionary_bytes = self._load_dictionary_bytes()
        self._decompressor = plocate.filename_index.build_zstd_decompressor(dictionary_bytes)

    @classmethod
    def open(cls, path: str) -> typing.Self:
        """Open a plocate database file from its path."""

        file_object = open(path, "rb")
        database = cls(file_object, path=path)

        return database

    @property
    def path(self) -> str | None:
        """Return the filesystem path passed to open(), if any."""

        return self._path

    @property
    def file_size(self) -> int:
        """Return the on-disk size of the database file in bytes."""

        return self._reader.file_size

    def close(self) -> None:
        """Close the underlying database file."""

        self._reader.close()

    def __enter__(self) -> typing.Self:
        """Enter a context manager that closes on exit."""

        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close the database when leaving a context manager."""

        self.close()

    def _load_dictionary_bytes(self) -> bytes | None:
        """Return the embedded zstd dictionary bytes, if present."""

        if self.header.version == 0:
            return None
        if self.header.zstd_dictionary_length_bytes == 0:
            return None

        dictionary_bytes = self._reader.read_bytes(
            self.header.zstd_dictionary_offset_bytes,
            self.header.zstd_dictionary_length_bytes,
        )

        return dictionary_bytes

    def filename_block_offsets(self) -> tuple[int, ...]:
        """Return the cached filename block offset table."""

        if self._filename_offsets is not None:
            return self._filename_offsets

        # Read and parse the uint64 offset index.
        index_length = (self.header.num_docids + 1) * 8
        index_bytes = self._reader.read_bytes(
            self.header.filename_index_offset_bytes,
            index_length,
        )
        offsets = plocate.filename_index.read_filename_block_offsets(
            index_bytes,
            self.header.num_docids,
        )
        self._filename_offsets = offsets

        return self._filename_offsets

    def read_configuration_block(self) -> list[plocate.config.ConfigurationEntry]:
        """Return updatedb configuration entries stored in the database."""

        if self.header.max_version < 2 or self.header.conf_block_length_bytes == 0:
            return []

        block_bytes = self._reader.read_bytes(
            self.header.conf_block_offset_bytes,
            self.header.conf_block_length_bytes,
        )
        entries = plocate.config.parse_configuration_block(block_bytes)

        return entries

    def _load_directory_time_entries(
        self,
    ) -> tuple[plocate.directory_data.DirectoryTimeEntry, ...] | None:
        """Return parsed directory timestamp entries, if present."""

        if self._directory_time_entries_loaded:
            return self._directory_time_entries

        self._directory_time_entries_loaded = True
        if self.header.max_version < 2:
            return None
        if self.header.directory_data_length_bytes == 0:
            return None

        # Read and decompress the parallel directory timestamp stream.
        compressed = self._reader.read_bytes(
            self.header.directory_data_offset_bytes,
            self.header.directory_data_length_bytes,
        )
        decompressed = plocate.directory_data.decompress_directory_data_bytes(compressed)
        entries = plocate.directory_data.parse_directory_time_entries(decompressed)
        self._directory_time_entries = entries

        return self._directory_time_entries

    def _load_trigram_index(self) -> plocate.trigram_index.TrigramIndex | None:
        """Return the parsed trigram index when present."""

        if self._trigram_index_loaded:
            return self._trigram_index

        self._trigram_index_loaded = True
        hash_table_offset = self.header.hash_table_offset_bytes
        hash_table_size = self.header.hashtable_size
        extra_hash_slots = self.header.extra_ht_slots
        entry_count = hash_table_size + extra_hash_slots + 1
        table_length = entry_count * plocate.trigram_index.TRIGRAM_STRUCT.size
        if hash_table_offset + table_length > self.file_size:
            return None

        # Read and parse the trigram hash table when it is present on disk.
        table_bytes = self._reader.read_bytes(hash_table_offset, table_length)
        table_entries = plocate.trigram_index.parse_trigram_table(table_bytes)
        self._trigram_index = plocate.trigram_index.TrigramIndex(
            self._reader,
            table_entries,
            hash_table_size=hash_table_size,
            extra_hash_slots=extra_hash_slots,
        )

        return self._trigram_index

    def has_trigram_index(self) -> bool:
        """Return whether this database contains a readable trigram index."""

        trigram_index = self._load_trigram_index()
        has_index = trigram_index is not None

        return has_index

    def trigram_index(self) -> plocate.trigram_index.TrigramIndex | None:
        """Return the parsed trigram index when present."""

        return self._load_trigram_index()

    def read_filename_block(self, docid: int) -> list[str]:
        """Return decompressed paths for one filename block docid."""

        offsets = self.filename_block_offsets()
        start = offsets[docid]
        end = offsets[docid + 1]
        compressed = self._reader.read_bytes(start, end - start)
        assert self._decompressor is not None
        block_paths = plocate.filename_index.decompress_filename_block(compressed, self._decompressor)

        return block_paths

    def iter_filename_blocks(self) -> collections.abc.Iterator[list[str]]:
        """Yield decompressed path lists for each filename block."""

        offsets = self.filename_block_offsets()
        assert self._decompressor is not None

        docid_indices = range(self.header.num_docids)
        for docid in docid_indices:
            block_paths = self.read_filename_block(docid)

            yield block_paths

    def iter_paths(self) -> collections.abc.Iterator[str]:
        """Yield every indexed path in document order."""

        blocks = self.iter_filename_blocks()
        for block_paths in blocks:
            for path in block_paths:
                yield path

    def iter_indexed_entries(self) -> collections.abc.Iterator[plocate.indexed_entry.IndexedEntry]:
        """Yield indexed paths with docid, header, and directory metadata."""

        directory_time_entries = self._load_directory_time_entries()
        directory_time_index = 0
        docid = 0

        # Walk filename blocks and pair each path with metadata in order.
        blocks = self.iter_filename_blocks()
        for block_paths in blocks:
            block_index = 0
            for path in block_paths:
                directory_time = None
                if directory_time_entries is not None:
                    if directory_time_index >= len(directory_time_entries):
                        message = "directory timestamp stream ended before indexed paths"
                        raise plocate.errors.PlocateFormatError(message)
                    directory_time = directory_time_entries[directory_time_index]
                    directory_time_index += 1

                entry = plocate.indexed_entry.IndexedEntry(
                    path=path,
                    docid=docid,
                    block_index=block_index,
                    database_version=self.header.version,
                    max_version=self.header.max_version,
                    check_visibility=self.header.check_visibility,
                    directory_time=directory_time,
                )
                yield entry
                block_index += 1

            docid += 1

        if directory_time_entries is not None and directory_time_index != len(directory_time_entries):
            message = "directory timestamp stream has {extra_count} extra entries".format(
                extra_count=len(directory_time_entries) - directory_time_index,
            )
            raise plocate.errors.PlocateFormatError(message)

    def statistics(self) -> plocate.stats.DatabaseStatistics:
        """Collect summary statistics for this database."""

        statistics = plocate.stats.collect_statistics(self)

        return statistics
