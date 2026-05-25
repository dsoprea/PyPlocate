"""Paths and search patterns for the updatedb fixture database."""

import os

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPDATEDB_DATABASE_PATH = os.path.join(_REPO_ROOT, "asset", "test", "test.db")
UPDATEDB_PYPROJECT_PATTERN = "pyproject.toml"
UPDATEDB_PYC_PATTERN = "test_stats.cpython-314-pytest-9.0.3.pyc"
