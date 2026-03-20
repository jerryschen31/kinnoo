# Task231 - feature28 registry config system (URL, token, tenant)

## Summary
- Added registry config loader module in src/kinnoo/config.py.
- Implemented `RegistryConfig` dataclass with fields:
  - `registry_url`
  - `registry_token`
  - `tenant_slug`
- Implemented `load_registry_config(config_path=None)` with precedence policy:
  1) environment variables
  2) config file values
  3) missing as `None`
- Added supported env var overrides:
  - `KINNOO_REGISTRY_URL`
  - `KINNOO_REGISTRY_TOKEN`
  - `KINNOO_TENANT_SLUG`
- Config file support implemented for `~/.kinnoo/config.yaml` by default, with optional path override for tests/callers.
- Added mapped test329 in tests/test_cli_env_vars.py as `test_registry_config_precedence`.
- Exported config API from src/kinnoo/__init__.py (`RegistryConfig`, `load_registry_config`).

## Tests and results
- `python3 -m pytest tests/test_cli_env_vars.py::test_registry_config_precedence` -> `1 passed`

## Bug/error notes
- Bug class: indentation error in test file after first insert.
- Attempts used for this bug class: `1` (cap: `5`).
- Fix: unindented the test function to module top-level.

## Teaching notes
- A dedicated config loader with explicit precedence order prevents configuration drift and makes CLI/backend selection deterministic.
- Using a dataclass for resolved config improves readability and type safety over passing raw dictionaries through the codebase.
- Accepting an optional config path is a testability best practice: unit tests avoid mutating user home directories and remain hermetic.
- Sanitizing/normalizing string values (trim + empty-to-None behavior) reduces subtle bugs caused by accidental whitespace or blank env var values.
