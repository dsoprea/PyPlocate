"""Search helpers and options."""

import collections.abc
import dataclasses
import logging

import plocate.patterns

_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass(slots=True)
class SearchOptions:
    """Options controlling plocate database searches."""

    ignore_case: bool = False
    match_basename: bool = False
    use_regex: bool = False
    extended_regex: bool = False
    limit: int | None = None

    def compile_patterns(self, patterns: tuple[str, ...]) -> list[plocate.patterns.CompiledPattern]:
        """Compile each pattern string using these search options."""

        if not patterns:
            raise ValueError("at least one search pattern is required")

        # Compile each user pattern with the configured search options.
        compiled_patterns: list[plocate.patterns.CompiledPattern] = []
        for pattern in patterns:
            compiled = self.compile_pattern(pattern)
            compiled_patterns.append(compiled)

        return compiled_patterns
    def compile_pattern(self, pattern: str) -> plocate.patterns.CompiledPattern:
        """Compile one pattern string using these search options."""

        compiled = plocate.patterns.compile_pattern(
            pattern,
            ignore_case=self.ignore_case,
            use_regex=self.use_regex,
            extended_regex=self.extended_regex,
        )

        return compiled


def search_paths(
    paths: collections.abc.Iterator[str],
    *patterns: str,
    options: SearchOptions | None = None,
) -> collections.abc.Iterator[str]:
    """Yield paths from paths that match every pattern."""

    if options is None:
        search_options = SearchOptions()
    else:
        search_options = options

    compiled_patterns = search_options.compile_patterns(patterns)

    # Scan paths and stop early when a limit is configured.
    match_count = 0
    for path in paths:
        matched = plocate.patterns.matches_all_patterns(
            compiled_patterns,
            path,
            match_basename=search_options.match_basename,
            ignore_case=search_options.ignore_case,
        )
        if matched:
            yield path
            match_count += 1
            if search_options.limit is not None and match_count >= search_options.limit:
                return


def search_database(
    database,
    *patterns: str,
    options: SearchOptions | None = None,
) -> collections.abc.Iterator[str]:
    """Search an open plocate database for paths matching every pattern."""

    path_iterator = database.iter_paths()
    filtered_iterator = search_paths(path_iterator, *patterns, options=options)

    yield from filtered_iterator
