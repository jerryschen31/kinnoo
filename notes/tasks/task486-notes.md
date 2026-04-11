# Task486 notes - Hotfix remote registry traceback handling (2026-04-10)

## What changed
- Added centralized remote registry error formatter in CLI dispatch.
- Caught `RemoteRegistryClientError` in `fetch`, `publish`, `list`, and `search` command paths.
- Replaced uncaught traceback behavior with concise stdout lines:
  - `[kinnoo] ERROR: <headline>`
  - `[kinnoo] Response: <server-json>` (when present)
- Added regression tests that assert non-zero exit, user-facing output, and absence of traceback text.

## Files updated
- src/kinnoo/cli.py
- tests/test_cli.py
- TASKS.txt
- TESTS.txt
- FEATURES.txt
- notes/features/feature115-swe-handoff.md

## Test run
- `python3 -m pytest tests/test_cli.py --testmon -k "remote_registry_errors_render_without_traceback_for_fetch_and_publish or remote_registry_errors_render_without_traceback_for_list_and_search"`
- `python3 src/validate_project_manifests.py`

## Teaching notes
- Catching transport/client exceptions at the CLI boundary keeps command modules focused on domain behavior while preserving a stable UX contract for human operators.
