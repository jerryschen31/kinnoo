# Task218 - feature39 violation diagnostics and secret-safe logging

## Summary
- Added [src/kinnoo/logging_utils.py](src/kinnoo/logging_utils.py):
	- shared helpers to format and emit structured violation diagnostics,
	- deterministic JSON rendering and secret-value redaction helper for diagnostics.
- Updated [src/kinnoo/install_trace.py](src/kinnoo/install_trace.py):
	- added `write_violation_event(...)` to append structured violation events to `.kinnoo/violation-events.jsonl`.
- Updated [src/kinnoo/sandbox.py](src/kinnoo/sandbox.py):
	- extended `SandboxDecision` with explicit `capability` and `action` fields,
	- preserved deterministic policy violation classification while improving structured context.
- Updated [src/kinnoo/run_command.py](src/kinnoo/run_command.py):
	- on sandbox denial, emits structured violation diagnostics with classification/capability/action/remediation,
	- persists run-boundary violation events via `.kinnoo/violation-events.jsonl`,
	- keeps diagnostics secret-safe by redacting forbidden values.
- Updated [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
	- emits structured install-boundary permission-consent violation diagnostics for denied/unsupported consent paths,
	- keeps event payloads actionable and value-safe.
- Updated [tests/test_run_preflight.py](tests/test_run_preflight.py):
	- added mapped test316 `test_feature39_violation_diagnostics_secret_safe`,
	- validates deterministic violation diagnostics include classification/capability/action/remediation,
	- validates no raw secret token leakage in stderr/stdout,
	- validates persisted violation event payload shape and secret-safe trace content.
- Updated [TASKS.txt](TASKS.txt):
	- `task218` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_run_preflight.py::test_feature39_violation_diagnostics_secret_safe` -> `1 passed`

## Bug/error notes
- One test placement issue caused a temporary syntax error in `tests/test_run_preflight.py` due to insertion before a `try/finally` block completed.
- Fixed by restoring the original `try/finally` structure and re-running mapped test successfully.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- Treat security diagnostics as first-class contracts: model them as structured events (`classification`, `capability`, `attempted_action`, `remediation`) so they are both human-actionable and machine-parseable.
- Keep redaction logic centralized (shared utility) to avoid drift and reduce accidental secret leakage across command paths.
- For regression tests around secret safety, assert both channels: user-facing output and persisted trace artifacts.
