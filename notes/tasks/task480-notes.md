# Task480 notes - server-side security check script (2026-04-10)

## What changed
- Added server-side post-publish security check service:
  - signature metadata check
  - archive structure integrity check
  - per-file integrity manifest check
- Added structured report output including per-check status/details and an aggregate `security_status` object.
- Added focused unit test coverage for pass/fail behavior.

## Files updated
- server/services/security_check.py
- server/tests/test_security_check.py
- TASKS.txt

## Design notes
- The service returns deterministic check records (`check_name`, `status`, `detail`) so later UI/API work can render concise status safely.
- `run_post_publish_checks_bytes` writes to a temporary `.kno` file and reuses the path-based checker, which keeps task481 integration simple when publish payloads are in-memory bytes.

## Test run
- `python3 -m pytest server/tests/test_security_check.py --testmon -k "post_publish_security_checks"`
  - Result: passed

## Teaching notes
- Modeling checks as explicit composable functions makes later execution-mode changes easier (local sync now, lambda async in task482) without changing output contracts.
