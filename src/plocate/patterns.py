"""Pattern matching compatible with plocate search semantics."""

import dataclasses
import enum
import fnmatch
import re



class PatternKind(enum.Enum):
    """How a compiled pattern should be matched against path text."""

    SUBSTRING = enum.auto()
    GLOB = enum.auto()
    REGEX = enum.auto()


WILDCARD_CHARACTERS = "*?["


@dataclasses.dataclass(frozen=True, slots=True)
class CompiledPattern:
    """A search pattern ready for repeated matching."""

    original: str
    kind: PatternKind
    value: str
    regular_expression: re.Pattern[str] | None = None


def _unescape_glob_to_plain_string(pattern: str) -> str:
    """Remove backslash escapes from a literal substring pattern."""

    plain_characters: list[str] = []
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if character == "\\":
            if index + 1 >= len(pattern):
                message = "pattern {pattern!r} ends with an escape character".format(pattern=pattern)
                raise ValueError(message)
            plain_characters.append(pattern[index + 1])
            index += 2
            continue
        if character in WILDCARD_CHARACTERS:
            message = "unexpected wildcard {character!r} while unescaping pattern".format(character=character)
            raise ValueError(message)
        plain_characters.append(character)
        index += 1
    joined = "".join(plain_characters)

    return joined


def compile_pattern(
    pattern: str,
    *,
    ignore_case: bool = False,
    use_regex: bool = False,
    extended_regex: bool = False,
) -> CompiledPattern:
    """Compile one user pattern into a matcher."""

    if use_regex:
        flags = 0
        if ignore_case:
            flags |= re.IGNORECASE
        compiled = re.compile(pattern, flags)

        return CompiledPattern(
            original=pattern,
            kind=PatternKind.REGEX,
            value=pattern,
            regular_expression=compiled,
        )

    if any(character in pattern for character in WILDCARD_CHARACTERS):
        return CompiledPattern(
            original=pattern,
            kind=PatternKind.GLOB,
            value=pattern,
        )

    if ignore_case:
        glob_pattern = "*{pattern}*".format(pattern=pattern)

        return CompiledPattern(
            original=pattern,
            kind=PatternKind.GLOB,
            value=glob_pattern,
        )

    plain_pattern = _unescape_glob_to_plain_string(pattern)

    return CompiledPattern(
        original=pattern,
        kind=PatternKind.SUBSTRING,
        value=plain_pattern,
    )


def _glob_match(pattern: str, haystack: str, *, ignore_case: bool) -> bool:
    """Return whether haystack matches the glob pattern."""

    if ignore_case:
        folded_haystack = haystack.casefold()
        folded_pattern = pattern.casefold()
        matched = fnmatch.fnmatch(folded_haystack, folded_pattern)

        return matched

    matched = fnmatch.fnmatch(haystack, pattern)

    return matched


def _matches_pattern(compiled_pattern: CompiledPattern, haystack: str, *, ignore_case: bool = False) -> bool:
    """Return whether haystack matches one compiled pattern."""

    if compiled_pattern.kind == PatternKind.SUBSTRING:
        if ignore_case:
            folded_haystack = haystack.casefold()
            folded_value = compiled_pattern.value.casefold()
            matched = folded_value in folded_haystack

            return matched

        matched = compiled_pattern.value in haystack

        return matched

    if compiled_pattern.kind == PatternKind.GLOB:
        matched = _glob_match(compiled_pattern.value, haystack, ignore_case=ignore_case)

        return matched

    assert compiled_pattern.regular_expression is not None
    search_result = compiled_pattern.regular_expression.search(haystack)
    matched = search_result is not None

    return matched


def matches_all_patterns(
    patterns: list[CompiledPattern],
    path: str,
    *,
    match_basename: bool,
    ignore_case: bool,
) -> bool:
    """Return whether path matches every compiled pattern."""

    haystack = path
    if match_basename:
        slash_index = path.rfind("/")
        if slash_index >= 0:
            haystack = path[slash_index + 1 :]
        else:
            haystack = path

    for pattern in patterns:
        matched = _matches_pattern(pattern, haystack, ignore_case=ignore_case)
        if not matched:
            return False

    return True
