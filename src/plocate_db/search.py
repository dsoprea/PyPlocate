"""Search helpers and options."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from plocate_db.patterns import CompiledPattern, compile_pattern, matches_all_patterns


@dataclass(slots=True)
class SearchOptions:
    ignore_case: bool = False
    match_basename: bool = False
    use_regex: bool = False
    extended_regex: bool = False
    limit: int | None = None

    def compile_patterns(self, patterns: tuple[str, ...]) -> list[CompiledPattern]:
        if not patterns:
            raise ValueError("at least one search pattern is required")
        return [self.compile_pattern(pattern) for pattern in patterns]

    def compile_pattern(self, pattern: str) -> CompiledPattern:
        return compile_pattern(
            pattern,
            ignore_case=self.ignore_case,
            use_regex=self.use_regex,
            extended_regex=self.extended_regex,
        )


def search_paths(
    paths: Iterator[str],
    *patterns: str,
    options: SearchOptions | None = None,
) -> Iterator[str]:
    search_options = options or SearchOptions()
    compiled_patterns = search_options.compile_patterns(patterns)

    match_count = 0
    for path in paths:
        if matches_all_patterns(
            compiled_patterns,
            path,
            match_basename=search_options.match_basename,
            ignore_case=search_options.ignore_case,
        ):
            yield path
            match_count += 1
            if search_options.limit is not None and match_count >= search_options.limit:
                return


def search_database(database, *patterns: str, options: SearchOptions | None = None) -> Iterator[str]:
    yield from search_paths(database.iter_paths(), *patterns, options=options)
