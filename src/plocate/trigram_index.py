"""Trigram hash table and posting list access."""

import dataclasses
import logging
import struct

import plocate.errors
import plocate.posting_list

_LOGGER = logging.getLogger(__name__)

TRIGRAM_STRUCT = struct.Struct("<IIQ")
WILDCARD_UNIGRAM = 0xFF000000
PREMATURE_END_UNIGRAM = 0xFF000001


@dataclasses.dataclass(frozen=True, slots=True)
class TrigramEntry:
    """One trigram hash table slot."""

    trigram: int
    num_docids: int
    offset_bytes: int


def hash_trigram(trigram: int, hash_table_size: int) -> int:
    """Hash one trigram value into a hash table bucket."""

    crc = trigram & 0xFFFFFFFF
    for _bit_index in range(32):
        bit = crc & 0x80000000
        crc = (crc << 1) & 0xFFFFFFFF
        if bit:
            crc ^= 0x1EDC6F41

    bucket = crc % hash_table_size

    return bucket


def parse_trigram_table(table_bytes: bytes) -> tuple[TrigramEntry, ...]:
    """Parse contiguous trigram hash table bytes."""

    if len(table_bytes) % TRIGRAM_STRUCT.size != 0:
        message = "trigram table length {length} is not a multiple of {entry_size}".format(
            length=len(table_bytes),
            entry_size=TRIGRAM_STRUCT.size,
        )
        raise plocate.errors.PlocateFormatError(message)

    entries: list[TrigramEntry] = []
    entry_count = len(table_bytes) // TRIGRAM_STRUCT.size
    for entry_index in range(entry_count):
        trigram, num_docids, offset_bytes = TRIGRAM_STRUCT.unpack_from(
            table_bytes,
            entry_index * TRIGRAM_STRUCT.size,
        )
        entry = TrigramEntry(
            trigram=trigram,
            num_docids=num_docids,
            offset_bytes=offset_bytes,
        )
        entries.append(entry)

    return tuple(entries)


def find_trigram_entry(
    table_entries: tuple[TrigramEntry, ...],
    trigram: int,
    hash_table_size: int,
    extra_hash_slots: int,
) -> TrigramEntry | None:
    """Look up one trigram in a parsed hash table."""

    bucket = hash_trigram(trigram, hash_table_size)
    probe_limit = extra_hash_slots + 1
    for probe_index in range(probe_limit + 1):
        entry = table_entries[bucket + probe_index]
        if entry.trigram == trigram:
            return entry

    return None


def posting_list_length_bytes(
    table_entries: tuple[TrigramEntry, ...],
    entry: TrigramEntry,
) -> int:
    """Return the byte length of one posting list using the sentinel offset."""

    entry_index = table_entries.index(entry)
    next_entry = table_entries[entry_index + 1]
    length_bytes = next_entry.offset_bytes - entry.offset_bytes

    return length_bytes


class TrigramIndex:
    """Parsed trigram hash table for one open database."""

    def __init__(
        self,
        reader,
        table_entries: tuple[TrigramEntry, ...],
        *,
        hash_table_size: int,
        extra_hash_slots: int,
    ) -> None:
        """Initialize a trigram index backed by one binary reader."""

        self._reader = reader
        self._table_entries = table_entries
        self._hash_table_size = hash_table_size
        self._extra_hash_slots = extra_hash_slots
        self._docid_cache: dict[int, tuple[int, ...]] = {}

    @property
    def hash_table_size(self) -> int:
        """Return the primary hash table size."""

        return self._hash_table_size

    @property
    def extra_hash_slots(self) -> int:
        """Return the number of overflow hash slots."""

        return self._extra_hash_slots

    def find_trigram_entry(self, trigram: int) -> TrigramEntry | None:
        """Return the hash table entry for trigram when present."""

        entry = find_trigram_entry(
            self._table_entries,
            trigram,
            self._hash_table_size,
            self._extra_hash_slots,
        )

        return entry

    def read_posting_list_docids(self, entry: TrigramEntry) -> tuple[int, ...]:
        """Decode the docid posting list for one trigram table entry."""

        if entry.trigram in self._docid_cache:
            return self._docid_cache[entry.trigram]

        length_bytes = posting_list_length_bytes(self._table_entries, entry)
        encoded = self._reader.read_bytes(entry.offset_bytes, length_bytes)
        docids = plocate.posting_list.decode_posting_list_docids(encoded, entry.num_docids)
        self._docid_cache[entry.trigram] = docids

        return docids
