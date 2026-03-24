# Task191 - feature34 OpenClaw template runnable via kinnoo run

## Summary
- Updated OpenClaw template runtime contract in [src/kinnoo/templates.py](src/kinnoo/templates.py):
  - `OPENCLAW_INDEX_MJS_TEMPLATE` now behaves as a minimal daemon entrypoint,
  - validates required environment variables (`OPENCLAW_API_KEY`, `KINNOO_TEST_SAFE_MODE`) before continuing,
  - emits deterministic startup/shutdown logs,
  - stays alive in daemon mode until terminated by `kinnoo stop`.
- Updated OpenClaw manifest template in [src/kinnoo/templates.py](src/kinnoo/templates.py):
  - added `env_vars` declaration for required runtime variables so `kinnoo run` pre-execution env resolution is enforced.
- Added task-linked smoke integration test in [tests/test_cli.py](tests/test_cli.py):
  - `test_feature34_openclaw_template_smoke_run` (test289),
  - initializes OpenClaw scaffold,
  - runs scaffold via `kinnoo run` with required env vars configured,
  - asserts deterministic non-empty startup output,
  - verifies daemon state/log files are created,
  - stops daemon and verifies state cleanup.
- Updated [TASKS.txt](TASKS.txt):
  - `task191` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli.py::test_feature34_openclaw_template_smoke_run` -> `1 passed`

## Bug/error notes
- Bug class 1: subprocess CLI script path failed under temporary working directory.
  - Cause: relative path (`src/kinnoo/cli.py`) was resolved from `tmp_path` during test execution.
  - Fix: compute absolute CLI script path from test file location using `Path(__file__).resolve().parents[1]`.
  - Same bug/error class fix attempts: `1`.

## Teaching notes
- For daemon scaffolds, a good first contract is: validate required env upfront, emit one deterministic readiness line, then keep process alive and handle SIGTERM cleanly.
- In CLI integration tests that use temp cwd, always build tool/script paths from repository-relative absolute paths; this avoids path drift and false negatives.
- Declaring `env_vars` in manifest plus template-side checks provides defense in depth:
  - `kinnoo run` enforces env presence before launch,
  - entrypoint validates runtime contract inside the process boundary.
