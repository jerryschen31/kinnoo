from __future__ import annotations

from pathlib import Path

import pytest

_MARKER_DESCRIPTIONS: dict[str, str] = {
    "regression_unit": "unit regression tests",
    "regression_integration": "integration regression tests",
    "regression_smoke": "smoke regression tests",
    "regression_uat": "user acceptance regression tests",
    "regression_sat": "system acceptance regression tests",
    "schema_contract": "schema/API contract tests",
    "schema_unit": "unit tests for in-memory schema validation",
    "integration": "integration tests",
    "e2e": "end-to-end workflow tests",
    "registry_client": "local registry client tests",
    "registry_remote": "remote registry contract tests",
    "server_api": "server-side API tests",
    "web_ui": "web frontend tests",
    "docs_contract": "documentation contract tests",
    "security_checks": "security and hardening tests",
    "ops": "operational/devops scripts and IaC tests",
}


def register_markers(config: pytest.Config) -> None:
    for marker, description in sorted(_MARKER_DESCRIPTIONS.items()):
        config.addinivalue_line("markers", f"{marker}: {description}")


def _add(item: pytest.Item, marker: str) -> None:
    item.add_marker(getattr(pytest.mark, marker))


def apply_auto_markers(items: list[pytest.Item]) -> None:
    for item in items:
        nodeid = item.nodeid.lower()
        path = Path(str(item.fspath)).as_posix().lower()
        name = item.name.lower()

        if "smoke" in name or "smoke" in nodeid:
            _add(item, "regression_smoke")
        if "uat" in name or "uat" in nodeid:
            _add(item, "regression_uat")
        if "sat" in name or "sat" in nodeid:
            _add(item, "regression_sat")
        if "schema_contract" in name or "schema_contract" in nodeid:
            _add(item, "schema_contract")

        if "/server/tests/" in path:
            _add(item, "server_api")
            _add(item, "integration")

        if path.startswith("tests/iac/"):
            _add(item, "ops")
            _add(item, "integration")
            _add(item, "regression_integration")

        if path.startswith("tests/registry_integration/"):
            _add(item, "integration")
            _add(item, "regression_integration")

        if "test_remote_client" in path:
            _add(item, "registry_remote")
            _add(item, "registry_client")

        if "test_trust_baseline.py" in path or "test_input_guard" in path or "security" in name:
            _add(item, "security_checks")

        if "test_oidc" in path or "test_web_auth" in path:
            _add(item, "server_api")
