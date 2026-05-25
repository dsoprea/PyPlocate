"""Binary header parsing for plocate.db files."""

from __future__ import annotations

import struct
from dataclasses import dataclass

PLOCATE_MAGIC = b"\0plocate"
HEADER_STRUCT = struct.Struct("<8s4I2Q2IQ6Q?7x")


@dataclass(frozen=True, slots=True)
class PlocateHeader:
    magic: bytes
    version: int
    hashtable_size: int
    extra_ht_slots: int
    num_docids: int
    hash_table_offset_bytes: int
    filename_index_offset_bytes: int
    max_version: int
    zstd_dictionary_length_bytes: int
    zstd_dictionary_offset_bytes: int
    directory_data_length_bytes: int
    directory_data_offset_bytes: int
    next_zstd_dictionary_length_bytes: int
    next_zstd_dictionary_offset_bytes: int
    conf_block_length_bytes: int
    conf_block_offset_bytes: int
    check_visibility: bool

    @classmethod
    def from_bytes(cls, data: bytes) -> PlocateHeader:
        if len(data) != HEADER_STRUCT.size:
            raise ValueError(f"expected {HEADER_STRUCT.size} header bytes, got {len(data)}")

        values = HEADER_STRUCT.unpack(data)
        header = cls(*values)
        if header.magic != PLOCATE_MAGIC:
            raise ValueError("magic number is not \\0plocate")
        if header.version not in (0, 1):
            raise ValueError(f"unsupported database version {header.version}")
        return header

    def to_bytes(self) -> bytes:
        return HEADER_STRUCT.pack(
            self.magic,
            self.version,
            self.hashtable_size,
            self.extra_ht_slots,
            self.num_docids,
            self.hash_table_offset_bytes,
            self.filename_index_offset_bytes,
            self.max_version,
            self.zstd_dictionary_length_bytes,
            self.zstd_dictionary_offset_bytes,
            self.directory_data_length_bytes,
            self.directory_data_offset_bytes,
            self.next_zstd_dictionary_length_bytes,
            self.next_zstd_dictionary_offset_bytes,
            self.conf_block_length_bytes,
            self.conf_block_offset_bytes,
            self.check_visibility,
        )
