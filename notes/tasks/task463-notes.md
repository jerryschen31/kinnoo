# Task463 - merge signing key into --sign

## Summary
- Removed standalone --signing-key option from pack CLI.
- Changed --sign to accept SIGNING_KEY directly: kinnoo pack --sign SIGNING_KEY <agent-dir>.
- Updated pack flow and tests to use the merged argument contract.

## Files changed
- src/kinnoo/cli.py
- src/kinnoo/pack_command.py
- tests/test_pack.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_pack.py --testmon -k "test_pack_sign_merged_argument"
- Result:
  - 1 passed, 32 deselected

## Teaching notes
- Consolidating tightly coupled flags reduces invalid combinations and simplifies both parser constraints and user mental model.
- Migration-safe testing should verify both the new success path and explicit rejection of removed legacy flags.
