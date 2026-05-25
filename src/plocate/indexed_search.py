"""Indexed candidate selection using the trigram hash table."""

import plocate.trigram_index
import plocate.trigram_patterns



def _union_sorted_docids(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    """Return the sorted union of two sorted docid tuples."""

    merged: list[int] = []
    left_index = 0
    right_index = 0
    while left_index < len(left) and right_index < len(right):
        left_value = left[left_index]
        right_value = right[right_index]
        if left_value < right_value:
            merged.append(left_value)
            left_index += 1
            continue
        if right_value < left_value:
            merged.append(right_value)
            right_index += 1
            continue
        merged.append(left_value)
        left_index += 1
        right_index += 1

    while left_index < len(left):
        merged.append(left[left_index])
        left_index += 1
    while right_index < len(right):
        merged.append(right[right_index])
        right_index += 1

    return tuple(merged)


def _intersect_sorted_docids(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    """Return the sorted intersection of two sorted docid tuples."""

    merged: list[int] = []
    left_index = 0
    right_index = 0
    while left_index < len(left) and right_index < len(right):
        left_value = left[left_index]
        right_value = right[right_index]
        if left_value < right_value:
            left_index += 1
            continue
        if right_value < left_value:
            right_index += 1
            continue
        merged.append(left_value)
        left_index += 1
        right_index += 1

    return tuple(merged)


def select_candidate_docids(
    trigram_index: plocate.trigram_index.TrigramIndex,
    trigram_groups: list[plocate.trigram_patterns.TrigramDisjunction],
) -> tuple[int, ...] | None:
    """Return candidate docids for trigram_groups, or None when no match is possible."""

    candidate_docids: tuple[int, ...] | None = None
    for disjunction in trigram_groups:
        group_docids: tuple[int, ...] | None = None
        remaining_alternatives = len(disjunction.trigram_alternatives)
        for trigram in disjunction.trigram_alternatives:
            table_entry = trigram_index.find_trigram_entry(trigram)
            remaining_alternatives -= 1
            if table_entry is None:
                if remaining_alternatives == 0 and group_docids is None:
                    return None
                continue

            posting_docids = trigram_index.read_posting_list_docids(table_entry)
            if group_docids is None:
                group_docids = posting_docids
            else:
                group_docids = _union_sorted_docids(group_docids, posting_docids)

        if group_docids is None:
            return None

        if candidate_docids is None:
            candidate_docids = group_docids
        else:
            candidate_docids = _intersect_sorted_docids(candidate_docids, group_docids)
            if not candidate_docids:
                return tuple()

    if candidate_docids is None:
        return tuple()

    return candidate_docids
