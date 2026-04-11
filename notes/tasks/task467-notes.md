# Task467 - publish structured JSON output

## Summary
- Added publish --json flag in CLI and wired through to publish command.
- Implemented structured JSON success/error payloads for publish automation.
- Preserved existing human-readable output for non-JSON publish runs.

## Files changed
- src/kinnoo/cli.py
- src/kinnoo/publish_command.py
- tests/test_publish_refactor.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_publish_refactor.py --testmon -k "test_publish_json_output"
- Result:
  - 1 passed, 5 deselected

## Teaching notes
- Automation modes are most reliable when stdout is reserved for a single parseable JSON document and all operator diagnostics are handled separately.
- Introduce JSON output as an additive path that does not change default operator UX; this minimizes migration risk for existing users.
