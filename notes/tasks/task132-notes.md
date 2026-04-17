# Task132 Notes - Feature21 implement real LangGraph runnable template

## Scope implemented
- Replaced placeholder `langgraph` template runtime behavior with a framework-native graph/state runnable flow.
- Added deterministic test-safe execution mode for CI/local runs without external API calls.
- Added task132-linked tests to verify framework-native graph markers and runnable behavior.

## Files changed
- `src/kinnoo/templates.py`
- `tests/test_init.py`
- `tests/test_cli.py`
- `TASKS.txt`

## Implementation details
- Updated `LANGGRAPH_RUN_PY` in `templates.py`:
  - Added `GraphState(TypedDict)` state schema.
  - Added `_build_graph()` with `StateGraph`, `START`, and `END` edges.
  - Added `_run_framework_mode(input_text)` using compiled graph invocation.
  - Added `_run_test_safe_mode(input_text)` deterministic local path.
  - Added `KINNOO_TEST_SAFE_MODE` env toggle and exception fallback to test-safe output.
- Updated `LANGGRAPH_README` with production graph path guidance and test-safe mode usage.
- Added `tests/test_init.py::test_feature21_langgraph_framework_native_template` (test196).
- Added `tests/test_cli.py::test_feature21_langgraph_basic_run` (test197) using CLI script-path invocation and test-safe mode.

## Tests implemented
- `tests/test_init.py::test_feature21_langgraph_framework_native_template` (test196)
- `tests/test_cli.py::test_feature21_langgraph_basic_run` (test197)

## Validation and regression results
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_init.py::test_feature21_langgraph_framework_native_template tests/test_cli.py::test_feature21_langgraph_basic_run -q` -> `2 passed`
- `python3 -m pytest tests/test_init.py -k "framework or feature21"` -> `21 passed, 16 deselected`
- `python3 -m pytest tests/test_cli.py -k "feature21"` -> `5 passed, 19 deselected`
- `python3 -m pytest tests/test_regression_v1.py -k "framework or feature21"` -> `1 passed, 2 deselected`
- `python3 -m pytest` -> skipped in this run (tool call explicitly skipped)

## Bug/error notes
- No implementation bug required fix iterations.
- 5-attempt cap was not approached.

## Teaching notes
- LangGraph centers on explicit state transitions: model your state schema first, then add nodes and edges as deterministic transformation steps.
- Keeping framework imports inside runtime functions helps templates remain runnable in fallback mode when dependencies are absent.
- For CLI smoke tests, deterministic test-safe outputs let you verify runtime contracts (exit code, output, no traceback) independent of network/API variability.
