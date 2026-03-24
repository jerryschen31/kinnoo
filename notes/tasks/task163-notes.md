# Task163 - feature19 import CLI surface and path resolution

## Summary
- Implemented task163 CLI surface for in-place import in [src/kinnoo/cli.py](src/kinnoo/cli.py):
  - Added `kinnoo import [path]` subcommand parser wiring
  - Added optional positional path argument with default behavior delegated to import command module
  - Wired dispatch to new import command handler
- Added new import command module [src/kinnoo/import_command.py](src/kinnoo/import_command.py):
  - `_resolve_import_target(target_path_arg)` resolves omitted path to current directory
  - `import_agent(target_path_arg)` validates path existence/type and starts import analysis flow placeholder for later tasks
- Added focused task163 tests in [tests/test_cli_import.py](tests/test_cli_import.py):
  - `test_feature19_import_defaults_to_current_directory` (test252)
  - `test_feature19_import_invalid_args_show_usage` (test253)
- Updated `task163` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_import.py::test_feature19_import_defaults_to_current_directory tests/test_cli_import.py::test_feature19_import_invalid_args_show_usage` -> `2 passed`

## Bug/error notes
- Encountered one test harness failure where invoking `src/kinnoo/cli.py` from a changed cwd caused file-not-found.
- Fixed by using absolute CLI script path computed from test file location.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- For CLI integration tests, path resolution in the test harness matters as much as product logic: use repository-anchored absolute paths whenever test `cwd` is intentionally varied.
- Separating parser wiring (`cli.py`) from command logic (`import_command.py`) keeps command surfaces stable and allows iterative feature delivery across dependent tasks.
- Task-scoped tests should validate contract behavior (default path and invalid forms) without overreaching into future task responsibilities (write flow, wizard, rollback).
