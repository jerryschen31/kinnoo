from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import CLI_COMMANDS
from tests.marker_tools import apply_auto_markers, register_markers


@pytest.fixture(scope="session")
def kinnoo_cli_commands() -> tuple[str, ...]:
    """Expose the current CLI command set for assertions in tests."""
    return CLI_COMMANDS


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def pytest_configure(config: pytest.Config) -> None:
    register_markers(config)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    apply_auto_markers(items)
