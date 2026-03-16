# Task158 - feature27 analyzer core API and report model

## Summary
- Added new analyzer library module at [src/kinnoo/analyzer.py](src/kinnoo/analyzer.py) with a stable public API:
  - `analyze_project(project_dir) -> AnalysisReport`
- Added report/data model primitives:
  - `DetectorResult` for value/confidence/evidence/warning detector outputs
  - `AnalysisReport` with stable top-level sections: `inferred`, `confidence`, `warnings`
- Implemented composable detector orchestration hooks with explicit per-field detector registry (`_detector_registry`).
- Added input validation for project path in `_validate_project_dir` and side-effect-free analyzer execution semantics.
- Added baseline task158 tests at [tests/test_analyzer.py](tests/test_analyzer.py):
  - `test_feature27_analyzer_public_api_and_detector_hooks` (test243)
  - `test_feature27_report_sections_are_stable` (test249)
  - `test_feature27_analyzer_reusable_for_feature19_import_flow` (test250)
- Updated `task158` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_analyzer.py::test_feature27_analyzer_public_api_and_detector_hooks tests/test_analyzer.py::test_feature27_report_sections_are_stable tests/test_analyzer.py::test_feature27_analyzer_reusable_for_feature19_import_flow` -> `3 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Designing analyzer outputs as a stable contract (`AnalysisReport` + `as_dict`) decouples downstream workflows from detector internals, which is a key pattern for agentic systems where components evolve independently.
- Confidence/evidence metadata is more robust than binary success/failure in uncertain inference systems; it enables human-in-the-loop review without hard-stopping automation.
- A detector registry pattern is interview-relevant because it shows extensibility and separation of concerns: orchestration stays fixed while detector capabilities expand incrementally.
