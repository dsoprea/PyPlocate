[![PyPI version](https://img.shields.io/pypi/v/plocate2)](https://pypi.org/project/plocate2/)

# Overview

Python library and command-line tools for reading [plocate](https://plocate.sesse.net) database files (`plocate.db`), the default 'locate' implementation of Arch, Debian, Ubuntu, and other Linux distributions.

This can enable an application to have immediate and optimized access to a reasonably up-to-date catalog of the complete filesystem and to *avoid the overhead of manually scanning every file*.

This not only requires a Linux system that has *plocate* installed and running, but that you can wait, or manage the reality of having to wait, for the next plocate update before you can see new files.

# Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

# Usage Via Library

Examples use the checked-in fixture at `asset/test/test.db` unless noted otherwise. That file is an `updatedb` snapshot of this repository, so paths in the output below are shown relative to the repository root (`./...`).

Search via the trigram index on a healthy database (substring or glob patterns):

```python
import plocate

with plocate.PlocateDatabase.open("asset/test/test.db") as database:
    options = plocate.SearchOptions(force_indexed_search=True)
    for path in plocate.search_database(database, "*.py", options=options):
        print(path)
```

```
./src/plocate/__init__.py
./src/plocate/binary_reader.py
./src/plocate/config.py
...
(37 paths)
```

Search via a full scan when the on-disk index is unreadable (for example, a truncated database):

```python
import plocate

with plocate.PlocateDatabase.open("truncated-plocate.db") as database:
    options = plocate.SearchOptions(force_linear_search=True)
    for path in plocate.search_database(database, "readme", options=options):
        print(path)
```

```
/tmp/example/readme.txt
```

`search_database` also scans every filename block on healthy databases when the pattern cannot use the index, such as regex searches:

```python
import plocate

options = plocate.SearchOptions(use_regex=True)
with plocate.PlocateDatabase.open("asset/test/test.db") as database:
    for path in plocate.search_database(database, r"\.py$", options=options):
        print(path)
```

```
./src/plocate/__init__.py
./src/plocate/binary_reader.py
./src/plocate/config.py
...
(37 paths)
```

Export indexed records:

```python
import plocate

options = plocate.ExportOptions(include_pattern="*.py")
with plocate.PlocateDatabase.open("asset/test/test.db") as database:
    for record in plocate.iter_export_records(database, options=options):
        print(record.to_dict())
```

```
{'path': './src/plocate/__init__.py', 'docid': 0, 'block_index': 21, 'database_version': 1, 'max_version': 2, 'check_visibility': True, 'is_directory': False}
{'path': './src/plocate/binary_reader.py', 'docid': 0, 'block_index': 22, 'database_version': 1, 'max_version': 2, 'check_visibility': True, 'is_directory': False}
...
(37 records)
```

Inspect indexed entries with metadata:

```python
import plocate

# Synthetic example database with /tmp/example/... paths.
with plocate.PlocateDatabase.open("example.db") as database:
    for entry in database.iter_indexed_entries():
        print(entry.path, entry.docid, entry.directory_time)
```

```
/tmp/example/.catalog-repository.yaml 0 None
/tmp/example/readme.txt 0 None
/var/log/syslog 0 None
```

The `plocate.db` format does not store a dedicated "last updated" timestamp. The closest equivalent is the on-disk modification time of the database file itself.

```python
import plocate

with plocate.PlocateDatabase.open("asset/test/test.db") as database:
    modification_time = database.file_mtime()
    print(modification_time)
```

```
1779677352.9139218
```

The package also reads configuration blocks, directory timestamp streams, and trigram posting lists from real `plocate.db` files produced by upstream `updatedb` / `plocate-build`.

# Usage Via Commandline

The project is primarily meant to be used as a library. The command-line tools (`pl_stats`, `pl_search`, `pl_export`) are provided for testing, diagnosing, and general convenience; they wrap the same APIs documented above.

Examples use `asset/test/test.db` unless noted otherwise. Paths are shown relative to the repository root where applicable.

Print database statistics:

```bash
pl_stats /var/lib/plocate/plocate.db
pl_stats --json asset/test/test.db
```

```
$ pl_stats /var/lib/plocate/plocate.db
database: /var/lib/plocate/plocate.db
file size: ...
indexed paths: ...
...

$ pl_stats --json asset/test/test.db
{
  "database_path": "asset/test/test.db",
  "path_count": 104,
  "num_docids": 4,
  "version": 1,
  "max_version": 2,
  ...
}
```

Search for paths:

```bash
pl_search asset/test/test.db pyproject.toml
pl_search /var/lib/plocate/plocate.db -c '*.py'
pl_search asset/test/test.db --regex 'pyproject\.toml$'
pl_search asset/test/test.db -i readme
pl_search asset/test/test.db -l 10 '*.py'
```

```
$ pl_search asset/test/test.db pyproject.toml
./pyproject.toml

$ pl_search /var/lib/plocate/plocate.db -c '*.py'
12345

$ pl_search asset/test/test.db --regex 'pyproject\.toml$'
./pyproject.toml

$ pl_search asset/test/test.db -i readme
./README.md
./.pytest_cache/README.md

$ pl_search asset/test/test.db -l 10 '*.py'
./src/plocate/__init__.py
./src/plocate/binary_reader.py
./src/plocate/config.py
./src/plocate/constants.py
./src/plocate/database.py
./src/plocate/directory_data.py
./src/plocate/errors.py
./src/plocate/export.py
./src/plocate/filename_index.py
./src/plocate/formatting.py
```

`pl_search` uses the database trigram index on healthy `plocate.db` files. Upstream `updatedb` / `plocate-build` always write the hash table and posting lists, so a complete database normally has an index. Substring and glob searches narrow candidate filename blocks through that hash table, then verify matches in those blocks.

If the file is truncated or header metadata points past EOF, the reader treats the index as absent and falls back to a full scan of every filename block. Results can still be correct, but the search is slower. Use `--scan` to force that path, or `--indexed` to require trigram-index search. Regex searches (`-r` / `--regex`) always use a full scan, even on healthy databases, because patterns are not indexed the same way.

Indexed search on a healthy database (typical case):

```bash
pl_search /var/lib/plocate/plocate.db '*.py'
pl_search asset/test/test.db --indexed '*.py'
```

```
$ pl_search asset/test/test.db --indexed '*.py'
./src/plocate/__init__.py
./src/plocate/binary_reader.py
./src/plocate/config.py
...
(37 paths)
```

Full-scan fallback when the on-disk index is unreadable (for example, a truncated copy of the same file):

```bash
# Same command; pl_search scans all path blocks instead of the hash table.
pl_search truncated-plocate.db readme
pl_search asset/test/test.db --scan '*.py'
```

```
$ pl_search truncated-plocate.db readme
/tmp/example/readme.txt

$ pl_search asset/test/test.db --scan '*.py'
./src/plocate/__init__.py
./src/plocate/binary_reader.py
./src/plocate/config.py
...
(37 paths)
```

Export indexed paths as JSON Lines:

```bash
pl_export asset/test/test.db
pl_export asset/test/test.db --include './src/plocate/*'
pl_export /var/lib/plocate/plocate.db --include '*.py'
```

```
$ pl_export asset/test/test.db | head -n 1
{"block_index": 0, "check_visibility": true, "database_version": 1, "directory_time_nanoseconds": ..., "directory_time_seconds": ..., "docid": 0, "is_directory": true, "max_version": 2, "path": "./.cursor"}

$ pl_export asset/test/test.db --include './src/plocate/*' | head -n 1
{"block_index": 21, "check_visibility": true, "database_version": 1, "docid": 0, "is_directory": false, "max_version": 2, "path": "./src/plocate/__init__.py"}

$ pl_export /var/lib/plocate/plocate.db --include '*.py' | head -n 1
{"block_index": ..., "path": "/usr/lib/python3.14/...", ...}
```

Each export row includes the path plus index and header metadata. When the database stores directory timestamps, directory entries also include `is_directory` and `directory_time_*` fields. Regular files include `is_directory: false` but do not store per-file timestamps.

Example export row:

```json
{
  "block_index": 1,
  "check_visibility": false,
  "database_version": 1,
  "docid": 0,
  "max_version": 1,
  "path": "/tmp/example/readme.txt"
}
```

# Layout

- Library modules: `src/plocate/`
- CLI entrypoints: `src/plocate/entrypoint/` (`pl_stats`, `pl_search`, `pl_export`)
- Tests mirror library paths under `tests/`

```bash
pip install -e ".[dev]"
pytest
```

Reading the database requires permission to open the file. On many systems `/var/lib/plocate/plocate.db` is readable only by the `locate` group or via the setgid `plocate` binary.
