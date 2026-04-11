# Task470 - install structured JSON output

## Summary
- Added install `--json` flag and enforced `--json` + `-y` requirement for non-interactive output mode.
- Added structured JSON install payload output for automation-friendly consumption.
- Kept existing human-readable install output path for non-JSON invocations.

## Files changed
- src/kinnoo/cli.py
- tests/test_cli_install.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli_install.py --testmon -k "test_install_json_output"
- Result:
  - 1 passed, 23 deselected

## Teaching notes
- JSON mode should produce one stable document on stdout so scripts can parse deterministically.
- Requiring non-interactive mode (`-y`) for JSON avoids mixed prompt/output streams and makes CLI automation reliable.
