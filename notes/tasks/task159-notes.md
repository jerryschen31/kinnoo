# Task159 - feature27 entrypoint runtime framework detectors

## Summary
- Implemented task159 detectors in [src/kinnoo/analyzer.py](src/kinnoo/analyzer.py):
  - `_detect_entrypoint` with common-layout and `__main__` discovery heuristics
  - `_detect_runtime` with python/runtime-type inference, requires-python extraction, and runtime port hints
  - `_detect_framework` via deterministic import-pattern matching with ambiguity downgrades
- Added supporting stdlib-first helpers for deterministic parsing and evidence capture:
  - `_iter_python_files`, `_has_main_guard`, `_detect_python_version_from_pyproject`, `_detect_runtime_port_hint`, `_collect_import_names`
- Added task159 associated uncertainty test in [tests/test_analyzer.py](tests/test_analyzer.py):
  - `test_feature27_detect_entrypoint_runtime_framework_with_uncertainty` (test244)
- Updated `task159` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_analyzer.py::test_feature27_detect_entrypoint_runtime_framework_with_uncertainty` -> `1 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- For inference systems, ambiguity handling is a feature, not a failure: confidence downgrades + warnings preserve reliability while still providing useful guesses.
- Import-pattern detectors should be deterministic and explicit; this keeps behavior explainable and avoids flakiness from fuzzy matching.
- A good runtime detector balances defaults with evidence: defaults keep output usable, while evidence strings make inferred fields auditable during onboarding workflows.
