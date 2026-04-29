# Task128 Notes - Add runnable smoke tests for new frameworks

## Scope implemented
- Added feature21 smoke tests to validate that newly generated framework templates are runnable through `kinnoo run` with a basic input.
- Covered all required task128 tests:
  - `test188`: PydanticAI smoke run
  - `test189`: LangGraph smoke run
  - `test190`: OpenAI Agents smoke run

## Files changed
- `tests/test_cli.py`
- `TASKS.txt`

## Implementation details
- Added `_run_feature21_smoke_framework()` helper in `tests/test_cli.py` to reduce duplication across three smoke tests.
- Smoke flow per framework:
  1. Run `kinnoo init <name> --framework <framework>` in a temporary directory.
  2. Apply test-safe runtime configuration by clearing generated `requirements.txt` (avoids network-dependent package installation in CI).
  3. Run `kinnoo run <dir> "hello"` and assert:
     - exit code is `0`,
     - stdout is non-empty,
     - framework-specific marker appears in stdout,
     - no traceback or runtime error banner appears in stderr.

## Tests implemented
- `tests/test_cli.py::test_feature21_pydanticai_smoke_run` (test188)
- `tests/test_cli.py::test_feature21_langgraph_smoke_run` (test189)
- `tests/test_cli.py::test_feature21_openai_agents_smoke_run` (test190)

## Validation and regression results
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_init.py -k "framework or feature21"` -> `16 passed, 16 deselected`
- `python3 -m pytest tests/test_cli.py -k "feature21"` -> `3 passed, 18 deselected`
- `python3 -m pytest tests/test_regression_v1.py -k "framework or feature21"` -> `0 selected (exit code 5)`
- `python3 -m pytest` -> `182 passed, 1 skipped`

## Issue/bug notes
- No code bug was encountered while implementing task128.
- One checklist command selected zero tests (`test_regression_v1.py -k "framework or feature21"`) and exited with code 5; this is expected for current coverage state before task129 adds feature21 regression-gate assertions.

## Teaching notes
- For integration smoke tests, isolate external volatility first: keep CI deterministic by neutralizing network-coupled setup paths unless the task explicitly validates dependency installation.
- Use one reusable helper for repeated scaffold-run assertions to keep tests concise and lower maintenance cost.
- Smoke-test assertions should focus on runtime contract signals (exit code, non-empty stdout, absence of runtime exceptions), not model quality or external SDK behavior.
- Sequencing matters: task127 validates scaffold content, task128 validates run-path executability, and task129 validates legacy regression behavior.
