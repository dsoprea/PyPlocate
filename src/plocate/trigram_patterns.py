"""Parse search patterns into trigram constraint groups."""

import dataclasses

import plocate.trigram_index



@dataclasses.dataclass(slots=True)
class TrigramDisjunction:
    """One AND-group of OR-ed trigram alternatives."""

    trigram_alternatives: list[int]


def _read_unigram(pattern: str, start: int) -> tuple[int, int]:
    """Read one pattern byte or wildcard marker from pattern."""

    if start >= len(pattern):
        return plocate.trigram_index.PREMATURE_END_UNIGRAM, 0
    character = pattern[start]
    if character == "\\":
        if start + 1 >= len(pattern):
            return plocate.trigram_index.PREMATURE_END_UNIGRAM, 1
        return ord(pattern[start + 1]), 2
    if character == "*" or character == "?":
        return plocate.trigram_index.WILDCARD_UNIGRAM, 1
    if character == "[":
        length = 1
        if start + length >= len(pattern):
            return plocate.trigram_index.PREMATURE_END_UNIGRAM, length
        if pattern[start + length] == "!":
            length += 1
        if start + length >= len(pattern):
            return plocate.trigram_index.PREMATURE_END_UNIGRAM, length
        if pattern[start + length] == "]":
            length += 1
        while True:
            if start + length >= len(pattern):
                return plocate.trigram_index.PREMATURE_END_UNIGRAM, length
            if pattern[start + length] == "]":
                return plocate.trigram_index.WILDCARD_UNIGRAM, length + 1
            length += 1

    return ord(character), 1


def _read_trigram(pattern: str, start: int) -> int:
    """Read one trigram value from pattern starting at start."""

    first_value, first_length = _read_unigram(pattern, start)
    if first_value in (
        plocate.trigram_index.WILDCARD_UNIGRAM,
        plocate.trigram_index.PREMATURE_END_UNIGRAM,
    ):
        return first_value
    second_value, second_length = _read_unigram(pattern, start + first_length)
    if second_value in (
        plocate.trigram_index.WILDCARD_UNIGRAM,
        plocate.trigram_index.PREMATURE_END_UNIGRAM,
    ):
        return second_value
    third_value, _third_length = _read_unigram(pattern, start + first_length + second_length)
    if third_value in (
        plocate.trigram_index.WILDCARD_UNIGRAM,
        plocate.trigram_index.PREMATURE_END_UNIGRAM,
    ):
        return third_value

    trigram = first_value | (second_value << 8) | (third_value << 16)

    return trigram


def _case_alternatives_for_byte(byte_value: int) -> list[int]:
    """Return case variants for one ASCII byte."""

    if 65 <= byte_value <= 90:
        return [byte_value, byte_value + 32]
    if 97 <= byte_value <= 122:
        return [byte_value, byte_value - 32]

    return [byte_value]


def _expand_trigram_case_alternatives(pattern: str, start: int) -> list[int]:
    """Return all case variants for one three-byte trigram window."""

    pattern_bytes = pattern.encode("utf-8", errors="surrogateescape")
    if start + 3 > len(pattern_bytes):
        return []

    byte_alternatives = [
        _case_alternatives_for_byte(pattern_bytes[start + offset])
        for offset in range(3)
    ]
    alternatives: set[int] = set()
    for first_byte in byte_alternatives[0]:
        for second_byte in byte_alternatives[1]:
            for third_byte in byte_alternatives[2]:
                trigram = first_byte | (second_byte << 8) | (third_byte << 16)
                alternatives.add(trigram)

    sorted_alternatives = sorted(alternatives)

    return sorted_alternatives


def _parse_trigrams(pattern: str, *, ignore_case: bool) -> list[TrigramDisjunction]:
    """Break pattern into trigram AND-groups used for indexed search."""

    if ignore_case:
        return _parse_trigrams_ignore_case(pattern)

    disjunctions: list[TrigramDisjunction] = []
    index = 0
    while index < len(pattern):
        unigram_value, unigram_length = _read_unigram(pattern, index)
        if unigram_length == 0:
            break
        trigram_value = _read_trigram(pattern, index)
        if trigram_value in (
            plocate.trigram_index.WILDCARD_UNIGRAM,
            plocate.trigram_index.PREMATURE_END_UNIGRAM,
        ):
            index += unigram_length
            continue

        disjunction = TrigramDisjunction(trigram_alternatives=[trigram_value])
        disjunctions.append(disjunction)
        index += unigram_length

    return disjunctions


def _parse_trigrams_ignore_case(pattern: str) -> list[TrigramDisjunction]:
    """Break pattern into case-insensitive trigram AND-groups."""

    pattern_bytes = pattern.encode("utf-8", errors="surrogateescape")
    if len(pattern_bytes) < 3:
        return []

    disjunctions: list[TrigramDisjunction] = []
    start_indices = range(0, len(pattern_bytes) - 2)
    for start_index in start_indices:
        alternatives = _expand_trigram_case_alternatives(pattern, start_index)
        if not alternatives:
            continue
        disjunction = TrigramDisjunction(trigram_alternatives=alternatives)
        disjunctions.append(disjunction)

    return disjunctions


def parse_search_trigrams(patterns: tuple[str, ...], *, ignore_case: bool) -> list[TrigramDisjunction]:
    """Combine trigram groups from every search pattern."""

    combined_groups: list[TrigramDisjunction] = []
    for pattern in patterns:
        pattern_groups = _parse_trigrams(pattern, ignore_case=ignore_case)
        combined_groups.extend(pattern_groups)

    return combined_groups
