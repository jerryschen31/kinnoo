# Task268 Notes - Preflight runtime.path venv check fix

Date: 2026-03-23

## Scope Completed
- Implemented and validated task268 behavior for preflight dependency checks when `runtime.path` is set and `.venv` is missing.
- Added regression tests mapped to test382 and test383 in `tests/test_run_preflight.py`.
- Updated task status in `TASKS.txt` to `needs-review`.

## Code and Test Changes
- `src/kinnoo/run_command.py`
  - Confirmed dependency preflight check now accepts `runtime_path_raw` and resolves it via `_resolve_runtime_path_executable(...)`.
  - If `.venv` is missing but `runtime.path` resolves to a valid executable, preflight returns PASS with informational message that venv will be created at run time.
  - If `.venv` is missing and no valid `runtime.path` is configured, existing FAIL behavior is preserved.

- `tests/test_run_preflight.py`
  - Added `test_preflight_pass_runtime_path_no_venv` (test382): verifies PASS with runtime.path + missing `.venv`.
  - Added `test_preflight_fail_no_runtime_path_no_venv` (test383): verifies FAIL with missing `.venv` and no runtime.path.

## Deprecated task254/task255 test handling
- `task254` and `task255` are deprecated in `TASKS.txt`.
- Marked `test356`-`test359` as deprecated in `TESTS.txt` and disabled automation execution (`automated: false`) with explicit `[agent]` deprecation notes.
- Added `tests/test_corpus_matrix.py` as a retired placeholder module with commented test functions and `[agent]` inline notes to preserve historical traceability.

## Targeted Regression Run
Command used:
```bash
/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests/test_run_preflight.py --testmon -k "test_preflight_pass_runtime_path_no_venv or test_preflight_fail_no_runtime_path_no_venv"
```

Result:
```text
2 passed, 11 deselected
```

Manifest validation:
```bash
/Users/jerry/.pyenv/versions/3.11.12/bin/python src/validate_project_manifests.py
```

Result:
```text
Validation passed: manifests are consistent
```

## Teaching Notes
- Preflight checks are a form of **static operational validation**: they assess run readiness without executing business logic.
- `runtime.path` acts as an **execution contract override**. Validating this path in preflight reduces false negatives and improves developer trust in diagnostics.
- This pattern mirrors AI agent deployment guardrails: separate “is the environment executable?” checks from “does the model/agent produce correct outputs?” checks.
