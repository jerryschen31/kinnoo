# Task484 notes - New kinnoo fetch command (2026-04-11)

## What changed
- Added a new `kinnoo fetch` command to download a registry archive into local archive storage without unpacking.
- Added `src/kinnoo/fetch_command.py` with remote/local resolution support.
- Added integrity verification for all fetches and signature enforcement in `--strict` mode.
- Added JSON output mode for machine-readable fetch results.
- Ensured temporary remote download artifacts are cleaned up on success and failure paths.

## Files updated
- src/kinnoo/cli.py
- src/kinnoo/fetch_command.py
- tests/test_cli.py
- TASKS.txt

## Test run
- `python3 -m pytest tests/test_cli.py --testmon -k "fetch_downloads_archive or fetch_strict_verification"`
  - Result: passed

## Teaching notes
- Reusing existing verifier helpers from install flow is a good hardening pattern: fetch and install now enforce identical archive trust checks while keeping command responsibilities separate (fetch stores only; install stores + unpacks).
