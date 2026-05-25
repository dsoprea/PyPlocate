"""Pattern matching compatible with plocate search semantics."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from enum import Enum, auto


class PatternKind(Enum):
    SUBSTRING = auto()
    GLOB = auto()
    REGEX = auto()


WILDCARD_CHARACTERS = "*?["


@dataclass(frozen=True, slots=True)
class CompiledPattern:
    original: str
    kind: PatternKind
    value: str
    regular_expression: re.Pattern[str] | None = None


def unescape_glob_to_plain_string(pattern: str) -> str:
    plain_characters: list[str] = []
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if character == "\\":
            if index + 1 >= len(pattern):
                raise ValueError(f"pattern {pattern!r} ends with an escape character")
            plain_characters.append(pattern[index + 1])
            index += 2
            continue
        if character in WILDCARD_CHARACTERS:
            raise ValueError(f"unexpected wildcard {character!r} while unescaping pattern")
        plain_characters.append(character)
        index += 1
    return "".join(plain_characters)


def compile_pattern(
    pattern: str,
    *,
    ignore_case: bool = False,
    use_regex: bool = False,
    extended_regex: bool = False,
) -> CompiledPattern:
    if use_regex:
        flags = 0
        if ignore_case:
            flags |= re.IGNORECASE
        return CompiledPattern(
            original=pattern,
            kind=PatternKind.REGEX,
            value=pattern,
            regular_expression=re.compile(pattern, flags),
        )

    if any(character in pattern for character in WILDCARD_CHARACTERS):
        return CompiledPattern(
            original=pattern,
            kind=PatternKind.GLOB,
            value=pattern,
        )

    if ignore_case:
        return CompiledPattern(
            original=pattern,
            kind=PatternKind.GLOB,
            value=f"*{pattern}*",
        )

    plain_pattern = unescape_glob_to_plain_string(pattern)
    return CompiledPattern(
        original=pattern,
        kind=PatternKind.SUBSTRING,
        value=plain_pattern,
    )


def _glob_match(pattern: str, haystack: str, *, ignore_case: bool) -> bool:
    if ignore_case:
        return fnmatch.fnmatch(haystack.casefold(), pattern.casefold())
    return fnmatch.fnmatch(haystack, pattern)


def matches_pattern(compiled_pattern: CompiledPattern, haystack: str, *, ignore_case: bool = False) -> bool:
    if compiled_pattern.kind == PatternKind.SUBSTRING:
        if ignore_case:
            return compiled_pattern.value.casefold() in haystack.casefold()
        return compiled_pattern.value in haystack

    if compiled_pattern.kind == PatternKind.GLOB:
        return _glob_match(compiled_pattern.value, haystack, ignore_case=ignore_case)

    assert compiled_pattern.regular_expression is not None
    return compiled_pattern.regular_expression.search(haystack) is not None


def matches_all_patterns(
    patterns: list[CompiledPattern],
    path: str,
    *,
    match_basename: bool,
    ignore_case: bool,
) -> bool:
    haystack = path
    if match_basename:
        slash_index = path.rfind("/")
        haystack = path[slash_index + 1 :] if slash_index >= 0 else path

    return all(matches_pattern(pattern, haystack, ignore_case=ignore_case) for pattern in patterns)
