# Test Organization and Marker Guide

This file describes the test strategy and organization for kinnoo.

This repository uses pytest markers to keep regression testing targeted and maintainable as CLI and platform features evolve.

## Marker Dimensions

- Regression dimension:
  - `regression_unit`
  - `regression_integration`
  - `regression_smoke`
  - `regression_uat`
  - `regression_sat`
- Surface dimension:
  - `client_cli_init`, `client_cli_run`, `client_cli_test`, `client_cli_install`, `client_cli_pack`
  - `client_cli_diff`, `client_cli_fetch`, `client_cli_uninstall`, `client_cli_keygen`, `client_cli_inspect`
  - `client_cli_publish`, `client_cli_list`, `client_cli_search`, `client_cli_login`, `client_cli_logout`
  - `client_cli_import`, `client_cli_check`, `client_cli_registry`
- Layer dimension: `schema_unit`, `integration`, `client_cli`, `e2e`
- Component dimension: `validator`, `analyzer`, `registry_client`, `registry_remote`, `server_api`, `web_ui`
- Cross-cutting sets: `schema_contract`, `docs_contract`, `security_checks`

## Selection Examples

- Run all tests:

  ```bash
  python3 -m pytest
  ```

- Run only tests for changed files:

  ```bash
  python3 -m pytest --testmon
  ```

- Run only regression tests:

  ```bash
  python3 -m pytest -m "regression_unit or regression_integration or regression_smoke or regression_uat or regression_sat"
  ```

- Exclude regression tests:

  ```bash
  python3 -m pytest -m "not (regression_unit or regression_integration or regression_smoke or regression_uat or regression_sat)"
  ```

- Run init command contract tests:

  ```bash
  python3 -m pytest -m "client_cli_init and schema_contract"
  ```

- Run schema-only validator tests:

  ```bash
  python3 -m pytest -m "validator and schema_unit"
  ```

- Run smoke acceptance slice:

  ```bash
  python3 -m pytest -m "regression_smoke"
  ```

- Run security-focused tests:

  ```bash
  python3 -m pytest -m security_checks
  ```

## Test Layers

- Schema unit tests:
  - Prefer `validate_manifest_data(data)` for in-memory rule checks.
  - Do not require on-disk file structure unless a rule explicitly needs path context.
- Integration validation tests:
  - Use `validate(path)` when testing file existence, relative path resolution, and real manifest loading.
- CLI tests:
  - Use helpers in [tests/helpers.py](tests/helpers.py) to avoid brittle command argv duplication.
- E2E tests:
  - Keep full-flow tests limited and focused on behavior contracts.

## Helper Module

Use [tests/helpers.py](tests/helpers.py) as the single source for CLI invocation:

- `run_cli([...])` for generic execution
- `run_command("init", ... )` for command-safe execution
- command-specific helpers like `run_init(...)`, `run_install(...)`, `run_pack(...)`

This reduces breakage when CLI argument grammar changes.

## Release Baseline Subfolders

These folders are now the release baseline for new tests. Existing tests can stay in place and migrate gradually.

The default rule should be:
- Each test function maps to exactly one primary non-regression folder (its functional home).
- Regression folders are execution overlays and may duplicate functional coverage by intent, not ownership.

Suggested functional (non-regression) top-level folders:
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
- `tests/client_cli_registry/` (shared registry workflow scenarios)
- `tests/validator_integration/`
- `tests/registry_integration/`
- `tests/security_checks/`
- `tests/docs_contract/`
- `tests/e2e_workflows/`

Suggested regression overlay folders:
- `tests/regression/unit/`
- `tests/regression/integration/`
- `tests/regression/smoke/`
- `tests/regression/uat/`
- `tests/regression/sat/`

Recommendation on your one-and-only-one mapping idea:
- Yes for non-regression ownership: exactly one functional folder per test.
- No for regression overlays: a test scenario can belong to one functional home while being selected into one regression class via marker (`regression_*`).

## Additional Notes
Keep exactly one primary functional home per test function
This should be enforced for non-regression organization.
Example: a test belongs in exactly one of schema_unit, client_cli_init, client_cli_install, validator_integration, registry_integration, docs_contract, etc.
Treat regression as an execution overlay, not ownership
Regression category should be marker-driven first.
Optional mirrored folders under tests/regression are useful for curated suites and release gates, but should not become the source of truth for test ownership.
Allow one explicit exception
True cross-surface workflow tests (for example init → pack → install → run) can live in a dedicated e2e workflow folder rather than forcing arbitrary command ownership
