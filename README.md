# plocate

Python library and command-line tools for reading [plocate](https://github.com/deepin-community/plocate) database files (`plocate.db`).

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

Print database statistics:

```bash
pl_stats /var/lib/plocate/plocate.db
pl_stats --json test.db
```

Search for paths:

```bash
pl_search -d test.db '.catalog-repository.yaml'
pl_search -c /var/lib/plocate/plocate.db '*.py'
pl_search --regex -d test.db 'catalog-repository\\.yaml$'
pl_search -i -d test.db readme
pl_search -l 10 -d test.db example
```

`pl_search` uses the database trigram index on healthy `plocate.db` files. Upstream `updatedb` / `plocate-build` always write the hash table and posting lists, so a complete database normally has an index. Substring and glob searches narrow candidate filename blocks through that hash table, then verify matches in those blocks.

If the file is truncated or header metadata points past EOF, the reader treats the index as absent and falls back to a full scan of every filename block. Results can still be correct, but the search is slower. Use `--scan` to force that path, or `--indexed` to require trigram-index search. Regex searches (`-r` / `--regex`) always use a full scan, even on healthy databases, because patterns are not indexed the same way.

Indexed search on a healthy database (typical case):

```bash
pl_search -d /var/lib/plocate/plocate.db '*.py'
pl_search --indexed -d test.db '*.py'
```

Full-scan fallback when the on-disk index is unreadable (for example, a truncated copy of the same file):

```bash
# Same command; pl_search scans all path blocks instead of the hash table.
pl_search -d truncated-plocate.db '*.py'
pl_search --scan -d test.db '*.py'
```

Export indexed paths as JSON Lines:

```bash
pl_export test.db
pl_export test.db --include '/tmp/example/*'
pl_export /var/lib/plocate/plocate.db --include '*.py'
```

Each export row includes the path plus index and header metadata. When the database stores directory timestamps, directory entries also include `is_directory` and `directory_time_*` fields. Regular files include `is_directory: false` but do not store per-file timestamps.

Example export row:

```json
{
  "block_index": 1,
  "check_visibility": false,
  "database_version": 1,
  "docid": 0,
  "max_version": 2,
  "path": "/tmp/example/readme.txt"
}
```

## Layout

- Library modules: `src/plocate/`
- CLI entrypoints: `src/plocate/entrypoint/` (`pl_stats`, `pl_search`, `pl_export`)
- Tests mirror library paths under `tests/`

```bash
pip install -e ".[dev]"
pytest
```

Reading the database requires permission to open the file. On many systems `/var/lib/plocate/plocate.db` is readable only by the `locate` group or via the setgid `plocate` binary.

## Library

Search via the trigram index on a healthy database (substring or glob patterns):

```python
import plocate.database
import plocate.search

with plocate.database.PlocateDatabase.open("test.db") as database:
    options = plocate.search.SearchOptions(force_indexed_search=True)
    for path in plocate.search.search_database(database, "*.py", options=options):
        print(path)
```

Search via a full scan when the on-disk index is unreadable (for example, a truncated database):

```python
import plocate.database
import plocate.search

with plocate.database.PlocateDatabase.open("truncated-plocate.db") as database:
    options = plocate.search.SearchOptions(force_linear_search=True)
    for path in plocate.search.search_database(database, "*.py", options=options):
        print(path)
```

`search_database` also scans every filename block on healthy databases when the pattern cannot use the index, such as regex searches:

```python
import plocate.database
import plocate.search

options = plocate.search.SearchOptions(use_regex=True)
with plocate.database.PlocateDatabase.open("test.db") as database:
    for path in plocate.search.search_database(database, r"\.py$", options=options):
        print(path)
```

Export indexed records:

```python
import plocate.database
import plocate.export

options = plocate.export.ExportOptions(include_pattern="/tmp/example/*")
with plocate.database.PlocateDatabase.open("test.db") as database:
    for record in plocate.export.iter_export_records(database, options=options):
        print(record.to_dict())
```

Inspect indexed entries with metadata:

```python
import plocate.database

with plocate.database.PlocateDatabase.open("test.db") as database:
    for entry in database.iter_indexed_entries():
        print(entry.path, entry.docid, entry.directory_time)
```

The package also reads configuration blocks, directory timestamp streams, and trigram posting lists from real `plocate.db` files produced by upstream `updatedb` / `plocate-build`.
