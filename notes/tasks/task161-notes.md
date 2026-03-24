# Task161 - feature27 assets and services detectors

## Summary
- Implemented task161 detectors in [src/kinnoo/analyzer.py](src/kinnoo/analyzer.py):
  - `_detect_assets` with deterministic candidate discovery from common model/data file extensions, common asset directories, and AST-discovered path literals
  - `_detect_services` with deterministic endpoint inference for redis/postgres/http literals and optional health-check hints
- Added path-safety filtering for asset literals:
  - blocks traversal-like/unsafe paths (`..`, absolute, home-relative)
  - emits actionable warning metadata when unsafe candidates are ignored
- Added supporting helpers to keep detector logic modular and testable:
  - `_looks_like_safe_relative_path`, `_candidate_asset_directories`, `_candidate_asset_files`, `_collect_string_literals`, `_collect_path_literal_assets`, `_extract_service_endpoints_from_tree`, `_service_type_from_endpoint`, `_health_check_hint`
- Added task161 associated tests in [tests/test_analyzer.py](tests/test_analyzer.py):
  - `test_feature27_detect_assets_with_path_safety_filter` (test247)
  - `test_feature27_detect_services_with_health_check_hints` (test248)
- Updated `task161` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_analyzer.py::test_feature27_detect_assets_with_path_safety_filter tests/test_analyzer.py::test_feature27_detect_services_with_health_check_hints` -> `2 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- For detector design, split signal extraction from decision logic: string/AST extraction helpers feed narrow detector rules, making behavior explainable and interview-friendly.
- Path safety is best enforced with explicit policy checks (absolute paths, `..`, home-relative) before touching the filesystem; this reduces traversal risk and noisy inference.
- Service inference benefits from endpoint-type normalization (`redis`, `postgres`, `http`) plus optional hints only when evidence is strong, which keeps outputs actionable without over-claiming certainty.
