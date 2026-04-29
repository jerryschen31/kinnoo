# Task461 - pack preflight dry-run

## Summary
- Updated pack --preflight behavior to produce a dry-run report instead of creating an archive.
- Dry-run now reports destination archive path, files that would be packaged, and estimated payload size.

## Files changed
- src/kinnoo/cli.py
- src/kinnoo/pack_command.py
- tests/test_pack.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_pack.py --testmon -k "test_pack_preflight_dry_run"
- Result:
  - 1 passed, 32 deselected

## Teaching notes
- Dry-run modes are safest when they reuse the exact selection pipeline used by real execution, then exit before side effects.
- A useful preflight report should answer three operator questions quickly: what will be included, where output goes, and how large it is expected to be.
