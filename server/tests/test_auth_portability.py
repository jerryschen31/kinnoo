from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.regression_integration
@pytest.mark.server_api
@pytest.mark.client_cli_registry
@pytest.mark.web_ui
def test_feature118_auth_portability_matrix() -> None:
    tests_manifest = Path("TESTS.txt").read_text(encoding="utf-8")

    expected_automation_paths = [
        "server/tests/test_feature118_oidc_auth.py::test_feature118_test707_valid_and_invalid_oidc_token_envelopes",
        "server/tests/test_feature118_oidc_auth.py::test_feature118_test708_provider_selection_fail_fast",
        "web/__tests__/feature118-auth-flow.test.tsx",
        "tests/client_cli_registry/test_feature118_cli_auth.py::test_feature118_test710_hosted_login_persists_full_auth_state",
        "tests/client_cli_registry/test_feature118_cli_auth.py::test_feature118_test711_refresh_and_logout_no_state",
        "server/tests/test_publish.py::test_feature118_identity_mapping_and_publish_ownership",
        "server/tests/test_config.py::test_feature118_provider_neutral_env_alignment",
        "server/tests/test_auth_route.py::test_feature118_legacy_auth_paths_disabled",
        "server/tests/test_auth_portability.py::test_feature118_auth_portability_matrix",
    ]

    for automation_path in expected_automation_paths:
        assert automation_path in tests_manifest

    assert Path("server/tests/test_feature118_oidc_auth.py").exists()
    assert Path("server/tests/test_publish.py").exists()
    assert Path("server/tests/test_config.py").exists()
    assert Path("server/tests/test_auth_route.py").exists()
    assert Path("tests/client_cli_registry/test_feature118_cli_auth.py").exists()
    assert Path("web/__tests__/feature118-auth-flow.test.tsx").exists()
