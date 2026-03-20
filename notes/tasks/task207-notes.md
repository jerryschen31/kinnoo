# Task207 - feature37 machine-readable audit and install decision trace

## Summary
- Added new trace module [src/kinnoo/install_trace.py](src/kinnoo/install_trace.py) to persist deterministic JSON trace artifacts at `.kinnoo/install-trace.json` under the installed target directory.
- Updated [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
  - Added Node install trace payload builder/writer integration.
  - Recorded deterministic schema fields for runtime, package manager, lifecycle script metadata, audit severity counts, and policy decisions.
  - Persisted trace for both blocked and allowed outcomes after audit evaluation.
- Added task-linked integration test in [tests/test_cli_install.py](tests/test_cli_install.py):
  - `test_feature37_install_trace_captures_audit_and_decisions` (test305),
  - validates trace schema and values in both default blocked path and explicit override path.
- Updated [TASKS.txt](TASKS.txt):
  - `task207` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_install.py::test_feature37_install_trace_captures_audit_and_decisions` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Machine-readable traces should be written with stable structure and deterministic key ordering so they are useful for both human review and automation.
- Security decisions are easiest to audit when policy inputs (`allow_vulnerable`, `ignore_scripts`) are persisted alongside decision outcomes and reasons.
- Keep trace payloads metadata-only to avoid accidental secret leakage; never include env var values, tokens, or command output that may contain sensitive data.
