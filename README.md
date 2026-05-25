# plocate-db

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
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Reading the database requires permission to open the file. On many systems `/var/lib/plocate/plocate.db` is readable only by the `locate` group or via the setgid `plocate` binary.

## Library

```python
from plocate_db import PlocateDatabase, search_database

with PlocateDatabase.open("test.db") as database:
    for path in search_database(database, ".catalog-repository.yaml"):
        print(path)
    print(database.statistics())
```
