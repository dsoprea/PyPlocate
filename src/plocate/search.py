"""Search helpers and options."""

import collections.abc
import dataclasses

import plocate.errors
import plocate.indexed_search
import plocate.patterns
import plocate.trigram_patterns



@dataclasses.dataclass(slots=True)
class SearchOptions:
    """Options controlling plocate database searches."""

    ignore_case: bool = False
    match_basename: bool = False
    use_regex: bool = False
    extended_regex: bool = False
    limit: int | None = None
    force_indexed_search: bool = False
    force_linear_search: bool = False

    def validate_search_mode(self) -> None:
        """Reject incompatible forced search mode combinations."""

        if self.force_indexed_search and self.force_linear_search:
            raise ValueError("cannot force both indexed and linear search")

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


def _search_paths(
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


def _search_database_linear(
    database,
    compiled_patterns: list[plocate.patterns.CompiledPattern],
    search_options: SearchOptions,
) -> collections.abc.Iterator[str]:
    """Scan every indexed path and yield matches."""

    path_iterator = database.iter_paths()
    match_count = 0
    for path in path_iterator:
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


def _search_database_indexed(
    database,
    compiled_patterns: list[plocate.patterns.CompiledPattern],
    search_options: SearchOptions,
    trigram_groups: list[plocate.trigram_patterns.TrigramDisjunction],
    *,
    fallback_to_linear: bool = True,
) -> collections.abc.Iterator[str]:
    """Use the trigram index to narrow filename blocks before matching."""

    trigram_index = database.trigram_index()
    if trigram_index is None:
        if fallback_to_linear:
            yield from _search_database_linear(database, compiled_patterns, search_options)

            return

        message = "database has no trigram index"
        raise plocate.errors.PlocateDatabaseError(message)

    candidate_docids = plocate.indexed_search.select_candidate_docids(trigram_index, trigram_groups)
    if candidate_docids is None:
        return

    # Verify pattern matches inside each candidate filename block.
    match_count = 0
    for docid in candidate_docids:
        block_paths = database.read_filename_block(docid)
        for path in block_paths:
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

    if options is None:
        search_options = SearchOptions()
    else:
        search_options = options

    search_options.validate_search_mode()
    compiled_patterns = search_options.compile_patterns(patterns)

    # Force a full scan of every filename block.
    if search_options.force_linear_search:
        yield from _search_database_linear(database, compiled_patterns, search_options)

        return

    # Force trigram-index search even when auto mode would scan instead.
    if search_options.force_indexed_search:
        if search_options.use_regex:
            raise ValueError("indexed search cannot be used with regex patterns")
        if not database.has_trigram_index():
            message = "database has no trigram index"
            raise plocate.errors.PlocateDatabaseError(message)

        trigram_groups = plocate.trigram_patterns.parse_search_trigrams(
            patterns,
            ignore_case=search_options.ignore_case,
        )
        if not trigram_groups:
            raise ValueError("pattern is too short for indexed search")

        yield from _search_database_indexed(
            database,
            compiled_patterns,
            search_options,
            trigram_groups,
            fallback_to_linear=False,
        )

        return

    # Regex searches and databases without an index fall back to a full scan.
    if search_options.use_regex or not database.has_trigram_index():
        yield from _search_database_linear(database, compiled_patterns, search_options)

        return

    trigram_groups = plocate.trigram_patterns.parse_search_trigrams(
        patterns,
        ignore_case=search_options.ignore_case,
    )
    if not trigram_groups:
        yield from _search_database_linear(database, compiled_patterns, search_options)

        return

    yield from _search_database_indexed(
        database,
        compiled_patterns,
        search_options,
        trigram_groups,
    )
