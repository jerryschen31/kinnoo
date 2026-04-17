# Test Organization and Marker Guide

This file describes the test strategy and organization for kinnoo.

This repository uses pytest markers to keep regression testing targeted and maintainable as CLI and platform features evolve.

## Marker Dimensions

- Regression dimension: `regression`, `smoke`, `contract`
- Surface dimension:
  - `kinnoo_init`, `kinnoo_run`, `kinnoo_test`, `kinnoo_install`, `kinnoo_pack`
  - `kinnoo_diff`, `kinnoo_fetch`, `kinnoo_uninstall`, `kinnoo_keygen`, `kinnoo_inspect`
  - `kinnoo_publish`, `kinnoo_list`, `kinnoo_search`, `kinnoo_login`, `kinnoo_logout`
  - `kinnoo_import`, `kinnoo_check`
- Layer dimension: `schema_unit`, `integration`, `cli`, `e2e`
- Component dimension: `validator`, `analyzer`, `registry_client`, `registry_remote`, `server_api`, `web_ui`
- Cross-cutting sets: `docs_contract`, `security_checks`

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
  python3 -m pytest -m regression
  ```

- Exclude regression tests:

  ```bash
  python3 -m pytest -m "not regression"
  ```

- Run init command contract tests:

  ```bash
  python3 -m pytest -m "kinnoo_init and contract"
  ```

- Run schema-only validator tests:

  ```bash
  python3 -m pytest -m "validator and schema_unit"
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
