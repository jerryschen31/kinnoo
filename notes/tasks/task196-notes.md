# Task196 - feature35 install restore flow with overwrite warning and force controls

## Summary
- Implemented feature35 state snapshot restore flow in [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
  - added `_restore_state_snapshots(...)` to map packed snapshot data from `state_snapshots/<state-dir>/...` to runtime state roots,
  - added `_iter_state_dir_paths(...)` to support both legacy string and structured state_dirs manifest entries,
  - default path is warning-first and non-destructive when destination state already exists,
  - explicit overwrite mode removes existing state root and restores snapshot content deterministically.
- Added install API wiring for explicit state overwrite control in [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
  - `install_agent(..., overwrite_state=False)` now accepts state overwrite control and forwards it through `_install_from_archive_path(...)`.
- Added CLI flag wiring in [src/kinnoo/cli.py](src/kinnoo/cli.py):
  - new install option `--state-overwrite`,
  - propagated into install command invocation as `overwrite_state=True` when requested.
- Added task-linked integration test294 in [tests/test_install.py](tests/test_install.py):
  - `test_feature35_install_state_overwrite_warning_and_force` validates:
    - default install warns and preserves existing extracted state,
    - explicit `--state-overwrite` replaces state with snapshot content.
- Updated [TASKS.txt](TASKS.txt):
  - `task196` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_install.py::test_feature35_install_state_overwrite_warning_and_force` -> `1 passed`

## Bug/error notes
- No implementation bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Warning-first restore behavior is an operations safety pattern: preserve runtime state by default, then require explicit operator intent for destructive overwrite.
- Snapshot restore should be namespace-driven and deterministic (`state_snapshots/<declared-root>/...`) to avoid ambiguity and make install behavior testable.
- Feature toggles like `--state-overwrite` are best threaded as explicit function parameters (not hidden global state), which improves testability and future policy extension.
