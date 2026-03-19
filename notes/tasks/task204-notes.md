# Task204 - feature37 Node audit severity summary

## Summary
- Updated [src/kinnoo/install_command.py](src/kinnoo/install_command.py) to run Node dependency audit after successful Node dependency installation.
- Added deterministic severity summary parsing for `critical`, `high`, `moderate`, and `low` values from `npm audit --json` output.
- Added stable operator output format:
  - `[kinnoo install] Node audit severity summary: critical=<n> high=<n> moderate=<n> low=<n>`
- Kept Python install path unchanged (no Node audit summary output for Python runtime agents).
- Added task-linked integration test302 in [tests/test_cli_install.py](tests/test_cli_install.py):
  - `test_feature37_node_audit_severity_summary`
  - verifies Node summary output and Python no-op behavior.
- Updated [TASKS.txt](TASKS.txt):
  - `task204` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_install.py::test_feature37_node_audit_severity_summary` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Security telemetry should be deterministic and machine-readable enough for future policy gates; stable key order and field names matter.
- Keep runtime-aware branching explicit so security checks apply only where relevant (Node agents here) and do not regress unrelated runtime paths.
- When external tools return non-zero for actionable findings (like `npm audit`), parse output first and separate reporting from policy decisions.
