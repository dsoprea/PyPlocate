"""Tests for plocate.patterns."""

import logging

import pytest

import plocate.patterns

_LOGGER = logging.getLogger(__name__)


def test_unescape_glob_to_plain_string():
    """Remove backslash escapes from a literal substring pattern."""

    plain = plocate.patterns._unescape_glob_to_plain_string(r"foo\.bar")
    assert plain == "foo.bar"


def test_unescape_rejects_trailing_backslash():
    """Reject patterns that end with a dangling escape character."""

    with pytest.raises(ValueError, match="escape character"):
        plocate.patterns._unescape_glob_to_plain_string("foo\\")


def test_compile_pattern_substring():
    """Compile a plain substring pattern without wildcards."""

    compiled = plocate.patterns.compile_pattern(".catalog-repository.yaml")
    assert compiled.kind == plocate.patterns.PatternKind.SUBSTRING
    assert plocate.patterns._matches_pattern(compiled, "/tmp/.catalog-repository.yaml")


def test_compile_pattern_glob():
    """Compile a glob pattern and match path suffixes."""

    compiled = plocate.patterns.compile_pattern("*.yaml")
    assert compiled.kind == plocate.patterns.PatternKind.GLOB
    assert plocate.patterns._matches_pattern(compiled, "example.yaml")
    assert not plocate.patterns._matches_pattern(compiled, "example.txt")


def test_compile_pattern_ignore_case():
    """Compile a case-insensitive glob pattern."""

    compiled = plocate.patterns.compile_pattern("readme", ignore_case=True)
    assert compiled.kind == plocate.patterns.PatternKind.GLOB
    assert plocate.patterns._matches_pattern(compiled, "/tmp/README.TXT", ignore_case=True)


def test_compile_pattern_regex():
    """Compile a regular expression pattern."""

    compiled = plocate.patterns.compile_pattern(r"catalog-repository\.yaml$", use_regex=True)
    assert compiled.kind == plocate.patterns.PatternKind.REGEX
    assert plocate.patterns._matches_pattern(compiled, "/tmp/.catalog-repository.yaml")
    assert not plocate.patterns._matches_pattern(compiled, "/tmp/.catalog-repository.yaml.bak")


def test_matches_all_patterns_requires_every_pattern():
    """Require every compiled pattern to match the same path."""

    patterns = [
        plocate.patterns.compile_pattern(".catalog-repository.yaml"),
        plocate.patterns.compile_pattern("example"),
    ]
    assert plocate.patterns.matches_all_patterns(
        patterns,
        "/tmp/example/.catalog-repository.yaml",
        match_basename=False,
        ignore_case=False,
    )
    assert not plocate.patterns.matches_all_patterns(
        patterns,
        "/tmp/other/.catalog-repository.yaml",
        match_basename=False,
        ignore_case=False,
    )


def test_matches_all_patterns_can_use_basename():
    """Match patterns against only the basename portion of each path."""

    patterns = [plocate.patterns.compile_pattern("readme.txt")]
    assert plocate.patterns.matches_all_patterns(
        patterns,
        "/tmp/example/readme.txt",
        match_basename=True,
        ignore_case=False,
    )
    assert not plocate.patterns.matches_all_patterns(
        patterns,
        "/tmp/readme.txt/extra",
        match_basename=True,
        ignore_case=False,
    )
