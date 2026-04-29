# Task478 - list add JSON option

## Summary
- Added `--json` to list parser.
- Implemented structured JSON list output mode for local and remote list results.
- Preserved existing line-by-line human-readable list output when `--json` is not set.

## Files changed
- src/kinnoo/cli.py
- src/kinnoo/list_command.py
- tests/test_cli_registry.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli_registry.py --testmon -k "test_list_json_output"
- Result:
  - 1 passed, 12 deselected

## Teaching notes
- JSON list APIs are easiest to consume when they always return the same envelope shape, including empty-result cases.
- Keep operator UX and automation UX separate: text mode for humans, JSON mode for machines.
