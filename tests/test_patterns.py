import pytest

from plocate_db.patterns import (
    PatternKind,
    compile_pattern,
    matches_all_patterns,
    matches_pattern,
    unescape_glob_to_plain_string,
)


def test_unescape_glob_to_plain_string():
    assert unescape_glob_to_plain_string(r"foo\.bar") == "foo.bar"


def test_unescape_rejects_trailing_backslash():
    with pytest.raises(ValueError, match="escape character"):
        unescape_glob_to_plain_string("foo\\")


def test_compile_pattern_substring():
    compiled = compile_pattern(".catalog-repository.yaml")
    assert compiled.kind == PatternKind.SUBSTRING
    assert matches_pattern(compiled, "/tmp/.catalog-repository.yaml")


def test_compile_pattern_glob():
    compiled = compile_pattern("*.yaml")
    assert compiled.kind == PatternKind.GLOB
    assert matches_pattern(compiled, "example.yaml")
    assert not matches_pattern(compiled, "example.txt")


def test_compile_pattern_ignore_case():
    compiled = compile_pattern("readme", ignore_case=True)
    assert compiled.kind == PatternKind.GLOB
    assert matches_pattern(compiled, "/tmp/README.TXT", ignore_case=True)


def test_compile_pattern_regex():
    compiled = compile_pattern(r"catalog-repository\.yaml$", use_regex=True)
    assert compiled.kind == PatternKind.REGEX
    assert matches_pattern(compiled, "/tmp/.catalog-repository.yaml")
    assert not matches_pattern(compiled, "/tmp/.catalog-repository.yaml.bak")


def test_matches_all_patterns_requires_every_pattern():
    patterns = [
        compile_pattern(".catalog-repository.yaml"),
        compile_pattern("example"),
    ]
    assert matches_all_patterns(
        patterns,
        "/tmp/example/.catalog-repository.yaml",
        match_basename=False,
        ignore_case=False,
    )
    assert not matches_all_patterns(
        patterns,
        "/tmp/other/.catalog-repository.yaml",
        match_basename=False,
        ignore_case=False,
    )


def test_matches_all_patterns_can_use_basename():
    patterns = [compile_pattern("readme.txt")]
    assert matches_all_patterns(
        patterns,
        "/tmp/example/readme.txt",
        match_basename=True,
        ignore_case=False,
    )
    assert not matches_all_patterns(
        patterns,
        "/tmp/readme.txt/extra",
        match_basename=True,
        ignore_case=False,
    )
