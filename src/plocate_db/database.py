"""Core plocate.db reader."""

from __future__ import annotations

from collections.abc import Iterator
from typing import BinaryIO, Self

import zstandard

from plocate_db.binary_reader import BinaryReader
from plocate_db.config import ConfigurationEntry, parse_configuration_block
from plocate_db.errors import PlocateFormatError
from plocate_db.filename_index import (
    build_zstd_decompressor,
    decompress_filename_block,
    read_filename_block_offsets,
)
from plocate_db.header import HEADER_STRUCT, PlocateHeader
from plocate_db.stats import DatabaseStatistics, collect_statistics


class PlocateDatabase:
    """Reader for a plocate.db index file."""

    def __init__(self, file_object: BinaryIO, *, path: str | None = None) -> None:
        self._reader = BinaryReader(file_object)
        self._path = path
        self._decompressor: zstandard.ZstdDecompressor | None = None
        self._filename_offsets: tuple[int, ...] | None = None

        header_bytes = self._reader.read_bytes(0, HEADER_STRUCT.size)
        try:
            self.header = PlocateHeader.from_bytes(header_bytes)
        except ValueError as error:
            raise PlocateFormatError(str(error)) from error

        dictionary_bytes = self._load_dictionary_bytes()
        self._decompressor = build_zstd_decompressor(dictionary_bytes)

    @classmethod
    def open(cls, path: str) -> Self:
        file_object = open(path, "rb")
        return cls(file_object, path=path)

    @property
    def path(self) -> str | None:
        return self._path

    @property
    def file_size(self) -> int:
        return self._reader.file_size

    def close(self) -> None:
        self._reader.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def _load_dictionary_bytes(self) -> bytes | None:
        if self.header.version == 0:
            return None
        if self.header.zstd_dictionary_length_bytes == 0:
            return None
        return self._reader.read_bytes(
            self.header.zstd_dictionary_offset_bytes,
            self.header.zstd_dictionary_length_bytes,
        )

    def filename_block_offsets(self) -> tuple[int, ...]:
        if self._filename_offsets is not None:
            return self._filename_offsets

        index_length = (self.header.num_docids + 1) * 8
        index_bytes = self._reader.read_bytes(
            self.header.filename_index_offset_bytes,
            index_length,
        )
        self._filename_offsets = read_filename_block_offsets(
            index_bytes,
            self.header.num_docids,
        )
        return self._filename_offsets

    def read_configuration_block(self) -> list[ConfigurationEntry]:
        if self.header.max_version < 2 or self.header.conf_block_length_bytes == 0:
            return []

        block_bytes = self._reader.read_bytes(
            self.header.conf_block_offset_bytes,
            self.header.conf_block_length_bytes,
        )
        return parse_configuration_block(block_bytes)

    def iter_filename_blocks(self) -> Iterator[list[str]]:
        offsets = self.filename_block_offsets()
        assert self._decompressor is not None

        for docid in range(self.header.num_docids):
            start = offsets[docid]
            end = offsets[docid + 1]
            compressed = self._reader.read_bytes(start, end - start)
            yield decompress_filename_block(compressed, self._decompressor)

    def iter_paths(self) -> Iterator[str]:
        for block_paths in self.iter_filename_blocks():
            yield from block_paths

    def statistics(self) -> DatabaseStatistics:
        return collect_statistics(self)
