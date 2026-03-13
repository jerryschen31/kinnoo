
## Task41 Summary — Remove Duplicate Test Functions + Add test63/test64

### Duplicate audit findings
- Duplicate function names were detected in the suite:
  - `test_cli_installable_and_runnable` defined in both `tests/test_cli.py` and `tests/test_init.py`
  - `test_manual_extraction_verifies_files` defined twice in `tests/test_pack.py`

### Consolidation changes
- Removed the duplicate `test_cli_installable_and_runnable` from `tests/test_init.py` (kept canonical version in `tests/test_cli.py`).
- Removed the second duplicate definition of `test_manual_extraction_verifies_files` in `tests/test_pack.py`.

### New tests for feature7
- Added `tests/test_suite_integrity.py::test_no_duplicate_test_functions` (test63):
  - AST-scans `tests/test_*.py`
  - fails on duplicate `test_*` function names across suite
- Added `tests/test_regression_v1.py::test_v1_suite_passes_after_feature7` (test64):
  - runs V1 module subset in subprocess
  - fails if any selected module regresses

### Bug uncovered and fixed during task41
- After deduplication, `test_manual_extraction_verifies_files` exposed a real packaging gap: manifest-declared extra files were not included in `.kno` archives.
- Fixed in `src/kinnoo/pack_command.py` by:
  - collecting additional files from manifest (`files` list and `extra_file` string)
  - validating existence and preventing path traversal outside agent dir
  - including safe additional files in archive output

### Validation runs
- `python3 -m pytest tests/test_pack.py::test_manual_extraction_verifies_files tests/test_regression_v1.py::test_v1_suite_passes_after_feature7` → `2 passed`
- `python3 -m pytest tests/test_suite_integrity.py tests/test_regression_v1.py tests/test_pack.py tests/test_init.py` → `32 passed`

### \[Agent] comments
- added in-line agent comments