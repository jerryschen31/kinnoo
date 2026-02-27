# Task39 Notes — Install Flow Modularization

Date: 2026-02-27

## Scope Completed
Implemented task39 (Feature7 AC1/AC2) by extracting install logic from the CLI into a dedicated module and verifying delegation behavior with test61.

## Code Changes
- Added new module: `src/kinnoo/install_command.py`
  - Implemented `install_agent(archive_path: str, target_dir_arg: str | None = None, force: bool = False) -> int`.
  - Moved install flow responsibilities into this function:
    - archive path/type validation (`.kno`)
    - target directory resolution and overwrite protection (`force` handling)
    - archive extraction
    - manifest presence and validation via `kinnoo.validator.validate`
    - `.venv` creation
    - wheel installation from `wheels/*.whl`
    - cleanup on failure and exit-code return semantics
- Updated `src/kinnoo/cli.py`
  - Replaced inline `install` branch implementation with delegation to `install_agent(...)`.
  - Preserved CLI usage behavior and force flag handling (`--force` via `sys.argv` check).
  - CLI now exits with the delegated function return code.

## Test Changes
- Updated `tests/test_cli_install.py`
  - Added `test_install_delegates_to_install_command` (test61) that verifies:
    1. structural delegation in the install branch (imports/calls `install_agent` and no inline extract/manifest logic), and
    2. behavioral continuity using a valid generated `.kno` archive and successful install.
  - Kept existing usage test for missing install argument.

## Regression/Validation Runs
### Targeted task39 test
- Command:
  - `python3 -m pytest tests/test_cli_install.py::test_install_delegates_to_install_command`
- Result:
  - `1 passed`

### Updated file sanity
- Command:
  - `python3 -m pytest tests/test_cli_install.py`
- Result:
  - `2 passed`

### Broader install regression
- Command:
  - `python3 -m pytest tests/test_install.py tests/test_cli_install.py tests/test_cli_install_extract.py tests/test_cli_install_manifest.py tests/test_cli_install_invalid.py tests/test_cli_install_wheels.py tests/test_cli_install_runnable.py`
- Result:
  - `9 passed`

## Follow-up Quality Fix
During regression, pytest warned about unknown `integration` marker. Added marker registration:
- Updated `pyproject.toml` with:
  - `[tool.pytest.ini_options]`
  - `markers = ["integration: marks integration tests"]`

Re-ran broader install regression after marker registration:
- Result: `9 passed`, warning removed.

## Outcome
Task39 implementation is complete and validated.
- Install logic is now modularized in `install_command.py`.
- `cli.py` delegates install operations cleanly.
- test61 added and passing.
- Broader install regressions pass.