# Task464 - pack --json structured output

## Summary
- Added pack --json flag and structured JSON payload on successful pack completion.
- Suppressed human-readable progress lines when --json is enabled.
- Added JSON-formatted error payload support for key failure paths.

## Files changed
- src/kinnoo/cli.py
- src/kinnoo/pack_command.py
- tests/test_pack.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_pack.py --testmon -k "test_pack_json_output"
- Result:
  - 1 passed, 32 deselected

## Teaching notes
- Machine-readable modes should emit a single deterministic stdout payload to keep downstream parsers robust.
- Preserve diagnostics on stderr while keeping stdout clean when automation mode is enabled.

## Verification snapshot
- Dedicated regression run completed during task464 step (`test_pack_json_output` passed).
