"""Build trigram hash tables for test plocate databases."""

import logging
import struct

import plocate.trigram_index

_LOGGER = logging.getLogger(__name__)

EXTRA_HASH_SLOTS = 16
TRIGRAM_MASK = 0xFFFFFF


def write_baseval(value: int) -> bytes:
    """Encode the first docid in a posting list."""

    if value < 128:
        return bytes([value])
    if value < 0x4000:
        return bytes([(value >> 8) | 0x80, value & 0xFF])
    if value < 0x200000:
        return bytes([(value >> 16) | 0xC0, value & 0xFF, (value >> 8) & 0xFF])
    if value < 0x10000000:
        return bytes([
            (value >> 24) | 0xE0,
            (value >> 16) & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        ])

    message = "docid {value} is too large for test posting lists".format(value=value)
    raise ValueError(message)


def extract_path_trigrams(path: str) -> set[int]:
    """Return trigrams extracted from one indexed path."""

    path_bytes = path.encode("utf-8")
    trigrams: set[int] = set()
    index = 0
    while index + 3 <= len(path_bytes):
        if path_bytes[index] == 0:
            index += 1
            continue
        if index + 1 < len(path_bytes) and path_bytes[index + 1] == 0:
            index += 2
            continue
        if index + 2 < len(path_bytes) and path_bytes[index + 2] == 0:
            index += 3
            continue

        trigram = path_bytes[index] | (path_bytes[index + 1] << 8) | (path_bytes[index + 2] << 16)
        trigrams.add(trigram & TRIGRAM_MASK)
        index += 1

    return trigrams


def collect_trigram_docids(paths: list[str]) -> dict[int, set[int]]:
    """Map trigrams to docid sets for one filename block."""

    trigram_docids: dict[int, set[int]] = {}
    for path in paths:
        path_trigrams = extract_path_trigrams(path)
        for trigram in path_trigrams:
            if trigram not in trigram_docids:
                trigram_docids[trigram] = set()
            trigram_docids[trigram].add(0)

    return trigram_docids


def _next_prime(minimum_size: int) -> int:
    """Return a small prime no smaller than minimum_size."""

    candidate = max(minimum_size, 3)
    while True:
        is_prime = True
        divisor = 2
        while divisor * divisor <= candidate:
            if candidate % divisor == 0:
                is_prime = False
                break
            divisor += 1
        if is_prime:
            return candidate
        candidate += 1


def _create_hash_table(
    trigram_docids: dict[int, tuple[int, ...]],
    hash_table_size: int,
) -> list[plocate.trigram_index.TrigramEntry]:
    """Build an open-addressed trigram hash table."""

    slot_count = hash_table_size + EXTRA_HASH_SLOTS + 1
    table_entries = [
        plocate.trigram_index.TrigramEntry(trigram=0xFFFFFFFF, num_docids=0, offset_bytes=0)
        for _slot_index in range(slot_count)
    ]
    sorted_trigrams = sorted(trigram_docids)
    for trigram in sorted_trigrams:
        docids = trigram_docids[trigram]
        pending_entry = plocate.trigram_index.TrigramEntry(
            trigram=trigram,
            num_docids=len(docids),
            offset_bytes=0,
        )
        bucket = plocate.trigram_index.hash_trigram(trigram, hash_table_size)
        distance = 0
        while table_entries[bucket].num_docids != 0:
            other_distance = bucket - plocate.trigram_index.hash_trigram(
                table_entries[bucket].trigram,
                hash_table_size,
            )
            if distance > other_distance:
                pending_entry, table_entries[bucket] = table_entries[bucket], pending_entry
                distance = other_distance
            bucket += 1
            distance += 1
            if distance > EXTRA_HASH_SLOTS:
                message = "failed to build test trigram hash table"
                raise ValueError(message)
        table_entries[bucket] = pending_entry

    return table_entries


def hash_table_size_for_paths(paths: list[str]) -> int:
    """Return the hash table size used for paths in test databases."""

    block_trigrams = collect_trigram_docids(paths)
    hash_table_size = _next_prime(max(len(block_trigrams), 1))

    return hash_table_size


def build_trigram_index_bytes(
    paths: list[str],
    *,
    posting_list_base: int,
) -> tuple[bytes, bytes]:
    """Build hash table and posting list bytes for one docid block."""

    trigram_docids_map: dict[int, set[int]] = {}
    block_trigrams = collect_trigram_docids(paths)
    for trigram, docids in block_trigrams.items():
        trigram_docids_map[trigram] = docids

    encoded_lists: dict[int, bytes] = {}
    sorted_trigrams = sorted(trigram_docids_map)
    for trigram in sorted_trigrams:
        docids = sorted(trigram_docids_map[trigram])
        encoded_lists[trigram] = write_baseval(docids[0])

    trigram_docids = {
        trigram: tuple(sorted(trigram_docids_map[trigram]))
        for trigram in sorted_trigrams
    }
    hash_table_size = _next_prime(len(sorted_trigrams))
    table_entries = _create_hash_table(trigram_docids, hash_table_size)

    posting_lists = bytearray()
    for entry_index in range(len(table_entries) - 1):
        entry = table_entries[entry_index]
        absolute_offset = posting_list_base + len(posting_lists)
        table_entries[entry_index] = plocate.trigram_index.TrigramEntry(
            trigram=entry.trigram,
            num_docids=entry.num_docids,
            offset_bytes=absolute_offset,
        )
        if entry.num_docids == 0:
            continue
        posting_lists.extend(encoded_lists[entry.trigram])

    sentinel_offset = posting_list_base + len(posting_lists)
    table_entries[-1] = plocate.trigram_index.TrigramEntry(
        trigram=0,
        num_docids=0,
        offset_bytes=sentinel_offset,
    )

    table_bytes = bytearray()
    for entry in table_entries:
        table_bytes.extend(
            plocate.trigram_index.TRIGRAM_STRUCT.pack(
                entry.trigram,
                entry.num_docids,
                entry.offset_bytes,
            )
        )

    return bytes(table_bytes), bytes(posting_lists), hash_table_size
