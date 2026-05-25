"""Binary header parsing for plocate.db files."""

import dataclasses
import struct


PLOCATE_MAGIC = b"\0plocate"
HEADER_STRUCT = struct.Struct("<8s4I2Q2IQ6Q?7x")


@dataclasses.dataclass(frozen=True, slots=True)
class PlocateHeader:
    """Fixed-layout header at the start of a plocate.db file."""

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
        """Parse a plocate header from exactly HEADER_STRUCT.size bytes."""

        if len(data) != HEADER_STRUCT.size:
            message = "expected {expected_size} header bytes, got {actual_size}".format(
                expected_size=HEADER_STRUCT.size,
                actual_size=len(data),
            )
            raise ValueError(message)

        # Unpack the fixed header and validate magic and version.
        values = HEADER_STRUCT.unpack(data)
        header = cls(*values)
        if header.magic != PLOCATE_MAGIC:
            raise ValueError("magic number is not \\0plocate")
        if header.version not in (0, 1):
            message = "unsupported database version {version}".format(version=header.version)
            raise ValueError(message)

        return header

    def to_bytes(self) -> bytes:
        """Serialize this header to HEADER_STRUCT.size bytes."""

        packed_bytes = HEADER_STRUCT.pack(
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

        return packed_bytes
