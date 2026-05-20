from __future__ import annotations

from pathlib import Path

import pytest

try:
    from tests.marker_tools import apply_auto_markers, register_markers
except ModuleNotFoundError:  # pragma: no cover - local pytest invocation fallback
    from marker_tools import apply_auto_markers, register_markers


_REGRESSION_MARKERS = {
    "regression_unit",
    "regression_integration",
    "regression_smoke",
    "regression_uat",
    "regression_sat",
}

_LAYER_MARKERS = {"schema_unit", "integration", "e2e"}

_SURFACE_COMPONENT_MARKERS = {
    "ops",
    "docs_contract",
    "registry_client",
    "registry_remote",
    "server_api",
    "security_checks",
}


def _ensure_marker_coverage(item: pytest.Item) -> None:
    names = {marker.name for marker in item.iter_markers()}
    path = Path(str(item.fspath)).as_posix().lower()

    if not (names & _REGRESSION_MARKERS):
        item.add_marker(pytest.mark.regression_integration)
        names = {marker.name for marker in item.iter_markers()}

    if not (names & _LAYER_MARKERS):
        if path.startswith("server/tests/") or path.startswith("tests/iac/") or path.startswith("tests/registry_integration/"):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.integration)
        names = {marker.name for marker in item.iter_markers()}

    if not (names & _SURFACE_COMPONENT_MARKERS):
        if path.startswith("tests/iac/"):
            item.add_marker(pytest.mark.ops)
        elif path.startswith("server/tests/"):
            item.add_marker(pytest.mark.server_api)
        elif "test_remote_client" in path:
            item.add_marker(pytest.mark.registry_remote)
        elif path.startswith("tests/registry_integration/"):
            item.add_marker(pytest.mark.server_api)
        else:
            item.add_marker(pytest.mark.ops)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def pytest_configure(config: pytest.Config) -> None:
    register_markers(config)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    apply_auto_markers(items)
    for item in items:
        _ensure_marker_coverage(item)
