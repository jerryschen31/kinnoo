# Task471 - run structured JSON output for non-openclaw agents

## Summary
- Implemented structured `kinnoo run --json` output for non-openclaw agents.
- Preserved OpenClaw JSON passthrough behavior (`--json` forwarded to delegated runtime).
- Added JSON envelope fields for automation, including timing, runtime metadata, policy state, and warnings.

## Files changed
- src/kinnoo/run_command.py
- src/kinnoo/cli.py
- tests/test_cli.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli.py --testmon -k "test_run_json_structured_output"
- Result:
  - 1 passed, 92 deselected

## Teaching notes
- CLI JSON modes are most stable when they emit a single document on stdout and avoid mixing human-facing progress lines into the same stream.
- For automation envelopes, include both machine-state fields (success/exit_code/error) and execution context (timing/runtime/input) so downstream systems can both validate outcomes and debug failures quickly.
