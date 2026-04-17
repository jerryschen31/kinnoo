from __future__ import annotations

import pytest

from tests.marker_tools import apply_auto_markers, register_markers


def pytest_configure(config: pytest.Config) -> None:
    register_markers(config)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    apply_auto_markers(items)
