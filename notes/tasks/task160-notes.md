# Task160 - feature27 dependencies and env var detectors

## Summary
- Implemented task160 detectors in [src/kinnoo/analyzer.py](src/kinnoo/analyzer.py):
  - `_detect_dependencies` with requirements/pyproject parsing, normalization, deduplication, and confidence-scored evidence
  - `_detect_env_vars` with AST-based extraction for `os.getenv(...)`, `os.environ[...]`, and `os.environ.get(...)`
- Added supporting deterministic helpers for parsing and formatting:
  - `_normalize_package_name`, `_split_requirement_name_and_constraint`, `_collect_requirements_dependencies`, `_collect_pyproject_dependencies`, `_format_dependency_output`, `_literal_string`, `_extract_env_var_names`
- Added task160 associated tests in [tests/test_analyzer.py](tests/test_analyzer.py):
  - `test_feature27_detect_dependencies_from_requirements_and_pyproject` (test245)
  - `test_feature27_detect_env_vars_patterns_and_dedup` (test246)
- Updated `task160` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_analyzer.py::test_feature27_detect_dependencies_from_requirements_and_pyproject tests/test_analyzer.py::test_feature27_detect_env_vars_patterns_and_dedup` -> `2 passed`

## Bug/error notes
- Encountered one failing test case where `os.environ.get(...)` was not detected due to AST condition nesting.
- Fixed by matching `os.environ.get(...)` in an independent call-shape branch.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- AST matching should model call-shapes explicitly; avoid over-nesting guards that accidentally constrain valid node forms.
- Dependency inference reliability improves when you separate parse, normalize, merge, and format stages; this makes failures easier to localize and test.
- Confidence scoring can reflect source breadth: detecting from both requirements and pyproject is a stronger signal than only one source.
