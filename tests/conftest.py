"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.fixture_builder import build_minimal_database_bytes


@pytest.fixture
def minimal_database_bytes() -> bytes:
    return build_minimal_database_bytes(
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


@pytest.fixture
def minimal_database_path(tmp_path: Path, minimal_database_bytes: bytes) -> Path:
    database_path = tmp_path / "minimal.plocate.db"
    database_path.write_bytes(minimal_database_bytes)
    return database_path
