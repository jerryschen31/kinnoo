from __future__ import annotations

from pathlib import Path

import pytest

_MARKER_DESCRIPTIONS: dict[str, str] = {
    "regression": "regression coverage tests",
    "smoke": "quick smoke validation tests",
    "contract": "contract-oriented compatibility tests",
    "kinnoo_init": "tests for kinnoo init command surface",
    "kinnoo_run": "tests for kinnoo run command surface",
    "kinnoo_test": "tests for kinnoo test command surface",
    "kinnoo_install": "tests for kinnoo install command surface",
    "kinnoo_pack": "tests for kinnoo pack command surface",
    "kinnoo_diff": "tests for kinnoo diff command surface",
    "kinnoo_fetch": "tests for kinnoo fetch command surface",
    "kinnoo_uninstall": "tests for kinnoo uninstall command surface",
    "kinnoo_keygen": "tests for kinnoo keygen command surface",
    "kinnoo_inspect": "tests for kinnoo inspect command surface",
    "kinnoo_publish": "tests for kinnoo publish command surface",
    "kinnoo_list": "tests for kinnoo list command surface",
    "kinnoo_search": "tests for kinnoo search command surface",
    "kinnoo_login": "tests for kinnoo login command surface",
    "kinnoo_logout": "tests for kinnoo logout command surface",
    "kinnoo_import": "tests for kinnoo import command surface",
    "kinnoo_check": "tests for kinnoo check command surface",
    "schema_unit": "unit tests for in-memory schema validation",
    "integration": "integration tests",
    "cli": "command-line behavior tests",
    "e2e": "end-to-end workflow tests",
    "validator": "validator module tests",
    "analyzer": "analyzer module tests",
    "registry_client": "local registry client tests",
    "registry_remote": "remote registry contract tests",
    "server_api": "server-side API tests",
    "web_ui": "web frontend tests",
    "docs_contract": "documentation contract tests",
    "security_checks": "security and hardening tests",
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

        if "regression" in name or "regression" in nodeid:
            _add(item, "regression")
        if "smoke" in name or "smoke" in nodeid:
            _add(item, "smoke")
        if "contract" in name or "contract" in nodeid:
            _add(item, "contract")

        if "/server/tests/" in path:
            _add(item, "server_api")
            _add(item, "integration")

        if path.endswith("test_web_frontend_setup.py"):
            _add(item, "web_ui")
            _add(item, "integration")

        if path.endswith("test_docs.py"):
            _add(item, "docs_contract")

        if "test_validator.py" in path:
            _add(item, "validator")
            if "entrypoint_path" in name or "entrypoints_union" in name:
                _add(item, "integration")
            elif "analyzer" in name:
                _add(item, "analyzer")
                _add(item, "integration")
            else:
                _add(item, "schema_unit")

        if "test_analyzer.py" in path:
            _add(item, "analyzer")
            _add(item, "integration")

        if "test_remote_client.py" in path:
            _add(item, "registry_client")
            _add(item, "registry_remote")
            _add(item, "integration")

        if "test_trust_baseline.py" in path or "test_input_guard" in path or "security" in name:
            _add(item, "security_checks")

        if "test_init.py" in path:
            _add(item, "kinnoo_init")
            _add(item, "cli")
            _add(item, "integration")
        if "test_cli.py" in path:
            _add(item, "cli")
            _add(item, "integration")
        if "test_cli_inspect.py" in path:
            _add(item, "kinnoo_inspect")
            _add(item, "cli")
            _add(item, "integration")
        if "test_pack" in path:
            _add(item, "kinnoo_pack")
            _add(item, "cli")
            _add(item, "integration")
        if "test_install" in path or "test_cli_install" in path:
            _add(item, "kinnoo_install")
            _add(item, "cli")
            _add(item, "integration")
        if "test_publish" in path:
            _add(item, "kinnoo_publish")
            _add(item, "cli")
            _add(item, "integration")
        if "test_run_preflight" in path:
            _add(item, "kinnoo_run")
            _add(item, "cli")
            _add(item, "integration")
        if "test_cli_import" in path:
            _add(item, "kinnoo_import")
            _add(item, "cli")
            _add(item, "integration")
        if "test_cli_registry" in path or "test_registry" in path:
            _add(item, "registry_remote")
            _add(item, "kinnoo_search")
            _add(item, "kinnoo_list")
            _add(item, "kinnoo_login")
            _add(item, "kinnoo_logout")
            _add(item, "kinnoo_fetch")
            _add(item, "kinnoo_publish")
            _add(item, "kinnoo_install")
            _add(item, "cli")
            _add(item, "integration")
        if "test_cli_remote_summary_shape" in path:
            _add(item, "registry_remote")
            _add(item, "integration")
        if "test_cli_openclaw_preflight" in path:
            _add(item, "kinnoo_check")
            _add(item, "cli")
            _add(item, "integration")
        if "test_archive_" in path:
            _add(item, "kinnoo_pack")
            _add(item, "kinnoo_install")
            _add(item, "integration")
