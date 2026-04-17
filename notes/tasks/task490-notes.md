# Task490 Notes - Regression Hardening (Helper Migration + Semantic Assertions)

## Scope Completed

This task pass focused on:

1. Continuing shared CLI helper migration for CLI-heavy test modules.
2. Continuing semantic assertion hardening for fragile help/output contracts.

Target modules:
- tests/test_cli_inspect.py
- tests/test_cli_install.py
- tests/test_cli_registry.py

## Changes Made

### 1) tests/test_cli_inspect.py

- Migrated all remaining direct CLI invocations from manual subprocess argv construction to shared helpers via tests/helpers.py.
- Standardized inspect calls through local wrapper:
  - _run_inspect(...)
  - backed by tests.helpers.run_command("inspect", ...)
- Replaced direct input=... subprocess usage with helper-compatible input_text=... flow.
- Added required run.py fixture in env-var inspect test where current validator enforces declared entrypoint path existence.
- Hardened brittle prompt assertions:
  - moved from exact full prompt sentence matching
  - to semantic fragments such as "Changing runtime.language" and "Proceed? (y/N):".
- Updated centralized-template guidance assertion to accept either entrypoint or entrypoints contracts.
- Updated invalid-runtime-language update test to use a genuinely unsupported value (ruby) rather than javascript.
- Cleaned stale imports after migration.

### 2) tests/test_cli_registry.py

- Migrated direct CLI subprocess invocations across publish/list/search/login/logout scenarios to shared helper usage.
- Added module-local helper wrapper:
  - _run_registry_command(command, *args, cwd=None, env=None, input_text=None)
  - delegates to tests.helpers.run_command(...)
- Removed hard dependency on local CLI_PATH construction for command execution paths.
- Hardened one fragile argument-error assertion:
  - from exact full parser message
  - to semantic checks requiring both "unrecognized arguments" and the removed flag token.
- Removed now-unused imports/constants from helper migration.

### 3) tests/test_cli_install.py

- Migrated large portions of direct CLI subprocess invocations to tests.helpers.run_command(...), including:
  - install usage/deprecated options/json flows
  - import flows in this test module
  - install delegation/fallback/offline flows
  - feature37 node audit and lifecycle sections
  - feature39 permission consent sections
  - feature40 unsigned warning sections
  - feature71 strict-install sections
  - feature72 frozen-install sections
  - feature74 uninstall confirmation sections
- Hardened usage assertion in missing-archive case to semantic prefix contract ("Usage: kinnoo install") rather than full pinned usage grammar.
- Removed unused helper/import artifacts after refactor.

## Validation Run Summary

Focused validation completed for migrated/hardened paths:

- python3 -m pytest tests/test_cli_inspect.py -q
  - PASS (20 passed)

- python3 -m pytest tests/test_cli_registry.py -q -k "feature56_local_publish_tenant_path or feature61_login_interactive_and_noninteractive or publish_preserves_all_versions or search_json_output or list_json_output or search_openclaw_skills_removed"
  - PASS (6 passed)

- python3 -m pytest tests/test_cli_install.py -q -k "install_missing_archive_prints_usage or install_deprecated_options_removed or install_openclaw_default_path or install_json_output or install_delegates_to_install_command or install_falls_back_to_pypi_when_wheel_missing or install_offline_succeeds_with_complete_wheels"
  - PASS (7 passed)

## Notes / Risk Context

- Full-module runs for registry/install still include pre-existing contract drift areas in this workspace (for example legacy node-audit flag expectations in parts of test_cli_install.py and auth policy behavior drift in parts of test_cli_registry.py).
- This pass preserved focus on task490 hardening goals:
  - helper migration progress,
  - reduced brittleness in assertions,
  - stability of migrated paths via focused execution.
