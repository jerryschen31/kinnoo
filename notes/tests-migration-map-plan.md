# Tests Migration Map Plan (Zero-Risk, Plan-Only)

Date: 2026-04-17
Scope: planning only. No file moves in this phase.

## Goal

Assign every current test file to one target folder so post-release moves can be batched without rethinking taxonomy.

## Rules Used

- One primary functional home per test file.
- Regression folders are overlays, not ownership, except for legacy gate files explicitly mapped there.
- Existing `server/tests/` files remain in place in this plan (no migration into `tests/` yet).
- This plan follows the release-baseline folders documented in `tests/README.md`.

## Target Folder Index

- `tests/schema_unit/`
- `tests/schema_contract/`
- `tests/client_cli_init/`
- `tests/client_cli_run/`
- `tests/client_cli_test/`
- `tests/client_cli_install/`
- `tests/client_cli_pack/`
- `tests/client_cli_diff/`
- `tests/client_cli_fetch/`
- `tests/client_cli_uninstall/`
- `tests/client_cli_keygen/`
- `tests/client_cli_inspect/`
- `tests/client_cli_publish/`
- `tests/client_cli_list/`
- `tests/client_cli_search/`
- `tests/client_cli_login/`
- `tests/client_cli_logout/`
- `tests/client_cli_import/`
- `tests/client_cli_check/`
- `tests/client_cli_registry/`
- `tests/validator_integration/`
- `tests/registry_integration/`
- `tests/security_checks/`
- `tests/docs_contract/`
- `tests/e2e_workflows/`
- `tests/regression/unit/`
- `tests/regression/integration/`
- `tests/regression/smoke/`
- `tests/regression/uat/`
- `tests/regression/sat/`

## Migration Map: `tests/`

| Current file | Target folder | Notes |
|---|---|---|
| `tests/test_analyzer.py` | `tests/validator_integration/` | Analyzer behavior and validator-adjacent integration coverage. |
| `tests/test_archive_integrity.py` | `tests/validator_integration/` | Archive validation/integrity behavior. |
| `tests/test_archive_path_traversal.py` | `tests/security_checks/` | Security hardening and traversal defense checks. |
| `tests/test_cli_env_vars.py` | `tests/e2e_workflows/` | Cross-command environment contract behavior. |
| `tests/test_cli_import.py` | `tests/client_cli_import/` | Primary import command surface. |
| `tests/test_cli_inspect.py` | `tests/client_cli_inspect/` | Primary inspect command surface. |
| `tests/test_cli_install_extract.py` | `tests/client_cli_install/` | Install workflow variant. |
| `tests/test_cli_install_invalid.py` | `tests/client_cli_install/` | Install invalid-input/error path coverage. |
| `tests/test_cli_install_manifest.py` | `tests/client_cli_install/` | Install manifest contract behavior. |
| `tests/test_cli_install_runnable.py` | `tests/client_cli_install/` | Install runnable behavior coverage. |
| `tests/test_cli_install_wheels.py` | `tests/client_cli_install/` | Install dependency/wheels coverage. |
| `tests/test_cli_install.py` | `tests/client_cli_install/` | Core install command suite. |
| `tests/test_cli_openclaw_preflight.py` | `tests/client_cli_check/` | Check/preflight command surface. |
| `tests/test_cli_registry_modes.py` | `tests/client_cli_registry/` | Registry command family behavior. |
| `tests/test_cli_registry.py` | `tests/client_cli_registry/` | Registry command family behavior. |
| `tests/test_cli_remote_summary_shape.py` | `tests/client_cli_registry/` | Registry remote summary contract behavior. |
| `tests/test_cli.py` | `tests/e2e_workflows/` | Multi-surface CLI behavior umbrella. |
| `tests/test_corpus_matrix.py` | `tests/e2e_workflows/` | Legacy matrix coverage artifact (currently retired). |
| `tests/test_docs.py` | `tests/docs_contract/` | Documentation contract checks. |
| `tests/test_feature_100.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_101.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_102.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_103.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_104.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_105.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_106.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_110.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_86.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_87.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_88.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_89.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_90.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_91.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_92.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_93.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_94.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_95.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_96.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_feature_99.py` | `tests/e2e_workflows/` | Feature acceptance workflow coverage. |
| `tests/test_health_check.py` | `tests/client_cli_check/` | Health/preflight-style service checks. |
| `tests/test_init.py` | `tests/client_cli_init/` | Core init command suite. |
| `tests/test_input_guard_integration.py` | `tests/security_checks/` | Security guard integration behavior. |
| `tests/test_input_guard.py` | `tests/security_checks/` | Security guard unit/integration behavior. |
| `tests/test_install_refactor.py` | `tests/client_cli_install/` | Install refactor behavior contracts. |
| `tests/test_install.py` | `tests/client_cli_install/` | Install and uninstall related behavior. |
| `tests/test_lambda_handler.py` | `tests/registry_integration/` | Registry metadata/security processing integration. |
| `tests/test_pack_refactor.py` | `tests/client_cli_pack/` | Pack refactor behavior contracts. |
| `tests/test_pack_robustness.py` | `tests/client_cli_pack/` | Pack robustness and edge coverage. |
| `tests/test_pack_size_reporting.py` | `tests/client_cli_pack/` | Pack reporting/output behavior. |
| `tests/test_pack.py` | `tests/client_cli_pack/` | Core pack command behavior. |
| `tests/test_publish_auth_diagnostics.py` | `tests/client_cli_publish/` | Publish auth diagnostics behavior. |
| `tests/test_publish_command.py` | `tests/client_cli_publish/` | Core publish command behavior. |
| `tests/test_publish_refactor.py` | `tests/client_cli_publish/` | Publish refactor behavior contracts. |
| `tests/test_registry.py` | `tests/client_cli_registry/` | Registry backend/service and registry-facing CLI behavior. |
| `tests/test_regression_v1.py` | `tests/regression/sat/` | Legacy regression gate location until retirement/removal. |
| `tests/test_remote_client.py` | `tests/registry_integration/` | Remote registry client integration behavior. |
| `tests/test_run_preflight.py` | `tests/client_cli_run/` | Run/preflight command surface behavior. |
| `tests/test_suite_integrity.py` | `tests/docs_contract/` | Suite governance and marker/docs integrity contracts. |
| `tests/test_trust_baseline.py` | `tests/security_checks/` | Trust and baseline security coverage. |
| `tests/test_validator.py` | `tests/schema_unit/` | Primary schema ownership; path-aware cases can split later to validator_integration. |
| `tests/test_web_frontend_setup.py` | `tests/e2e_workflows/` | End-to-end setup path for web frontend flow. |

## Migration Map: `server/tests/` (No Move in This Phase)

These files are intentionally assigned to remain under `server/tests/` for release safety.

| Current file | Target folder | Notes |
|---|---|---|
| `server/tests/test_agents_routes.py` | `server/tests/` | Keep server API tests in server test tree. |
| `server/tests/test_auth_route.py` | `server/tests/` | Keep server API/auth tests in server test tree. |
| `server/tests/test_bootstrap.py` | `server/tests/` | Keep server bootstrap tests in server test tree. |
| `server/tests/test_download.py` | `server/tests/` | Keep server API tests in server test tree. |
| `server/tests/test_jwt_auth.py` | `server/tests/` | Keep server auth/security tests in server test tree. |
| `server/tests/test_metadata.py` | `server/tests/` | Keep server metadata contract tests in server test tree. |
| `server/tests/test_middleware.py` | `server/tests/` | Keep server middleware tests in server test tree. |
| `server/tests/test_publish.py` | `server/tests/` | Keep server publish API tests in server test tree. |
| `server/tests/test_search.py` | `server/tests/` | Keep server search API tests in server test tree. |
| `server/tests/test_security_check.py` | `server/tests/` | Keep server security tests in server test tree. |
| `server/tests/test_session_auth.py` | `server/tests/` | Keep server session/auth tests in server test tree. |
| `server/tests/test_storage.py` | `server/tests/` | Keep server storage tests in server test tree. |
| `server/tests/test_templates.py` | `server/tests/` | Keep server template tests in server test tree. |
| `server/tests/test_tenant_model.py` | `server/tests/` | Keep server tenant model tests in server test tree. |
| `server/tests/test_user_model.py` | `server/tests/` | Keep server user model tests in server test tree. |
| `server/tests/test_web_agents.py` | `server/tests/` | Keep server web-agent tests in server test tree. |
| `server/tests/test_web_auth.py` | `server/tests/` | Keep server web auth tests in server test tree. |

## Batch Move Order (Post-Release)

1. Low-risk command folders first: `client_cli_inspect`, `client_cli_import`, `client_cli_run`, `client_cli_check`.
2. High-volume command folders next: `client_cli_install`, `client_cli_pack`, `client_cli_publish`, `client_cli_registry`.
3. Cross-cutting buckets: `security_checks`, `docs_contract`, `validator_integration`, `schema_unit`.
4. Feature/e2e bucket last: `e2e_workflows` (feature files and broad umbrella CLI files).
5. Legacy gate handling: retire or replace `test_regression_v1.py` after replacement suites are stable.

## Notes for Execution Phase

- Keep import paths stable during moves (use `git mv` in small batches).
- Run targeted suites after each batch with marker filters matching destination folder purpose.
- Do not co-migrate server tests in this release cycle.
- Split `tests/test_validator.py` into `schema_unit` and `validator_integration` only after helper fixture extraction is completed.
