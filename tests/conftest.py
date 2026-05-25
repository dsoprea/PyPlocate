"""Shared pytest fixtures."""

import logging
import os

import pytest

import tests.support.fixture_builder
import tests.support.updatedb_fixture
import plocate.directory_data

_LOGGER = logging.getLogger(__name__)

UPDATEDB_DATABASE_PATH = tests.support.updatedb_fixture.UPDATEDB_DATABASE_PATH
UPDATEDB_PYPROJECT_PATTERN = tests.support.updatedb_fixture.UPDATEDB_PYPROJECT_PATTERN
UPDATEDB_PYC_PATTERN = tests.support.updatedb_fixture.UPDATEDB_PYC_PATTERN


@pytest.fixture
def updatedb_database_path() -> str:
    """Return the path to the real updatedb fixture under asset/test/."""

    if not os.path.isfile(UPDATEDB_DATABASE_PATH):
        message = "updatedb fixture missing at {path}".format(path=UPDATEDB_DATABASE_PATH)
        pytest.fail(message)

    return UPDATEDB_DATABASE_PATH


@pytest.fixture
def minimal_database_bytes() -> bytes:
    """Return bytes for a minimal plocate database with sample paths."""

    database_bytes = tests.support.fixture_builder.build_minimal_database_bytes(
        [
            "/tmp/example/.catalog-repository.yaml",
            "/tmp/example/readme.txt",
            "/var/log/syslog",
        ],
        configuration_entries={
            "prune_bind_mounts": ["0"],
            "prunepaths": ["/tmp"],
        },
    )

    return database_bytes


@pytest.fixture
def minimal_database_path(tmp_path, minimal_database_bytes: bytes) -> str:
    """Write the minimal database bytes to a temporary file and return its path."""

    database_path = os.path.join(str(tmp_path), "minimal.plocate.db")
    with open(database_path, "wb") as database_file:
        database_file.write(minimal_database_bytes)

    return database_path


@pytest.fixture
def directory_timed_database_bytes() -> bytes:
    """Return bytes for a database with directory timestamp metadata."""

    database_bytes = tests.support.fixture_builder.build_minimal_database_bytes(
        [
            "/tmp/example",
            "/tmp/example/readme.txt",
            "/var/log/syslog",
        ],
        configuration_entries={
            "prune_bind_mounts": ["0"],
            "prunepaths": ["/tmp"],
        },
        directory_time_entries=[
            plocate.directory_data.DirectoryTimeEntry(
                is_directory=True,
                seconds=1700000000,
                nanoseconds=123456789,
            ),
            plocate.directory_data.DirectoryTimeEntry(is_directory=False),
            plocate.directory_data.DirectoryTimeEntry(is_directory=False),
        ],
    )

    return database_bytes


@pytest.fixture
def directory_timed_database_path(tmp_path, directory_timed_database_bytes: bytes) -> str:
    """Write the directory-timed database bytes to a temporary file."""

    database_path = os.path.join(str(tmp_path), "directory-timed.plocate.db")
    with open(database_path, "wb") as database_file:
        database_file.write(directory_timed_database_bytes)

    return database_path


@pytest.fixture
def truncated_database_path(tmp_path, minimal_database_bytes: bytes) -> str:
    """Write a truncated copy of the minimal database without a readable trigram index."""

    database_path = os.path.join(str(tmp_path), "truncated.plocate.db")
    truncated_bytes = minimal_database_bytes[:200]
    with open(database_path, "wb") as database_file:
        database_file.write(truncated_bytes)

    return database_path
