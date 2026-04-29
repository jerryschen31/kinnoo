# Task473 - inspect structured JSON output

## Summary
- Added `--json` to `kinnoo inspect` CLI parser and dispatch.
- Implemented JSON output paths for directory, archive, and clawhub mirror inspect targets.
- Added JSON output support for inspect update result payloads.
- Preserved existing human-readable inspect output behavior when `--json` is not used.

## Files changed
- src/kinnoo/cli.py
- src/kinnoo/inspect_command.py
- tests/test_cli_inspect.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli_inspect.py --testmon -k "test_inspect_json_output"
- Result:
  - 1 passed, 15 deselected

## Teaching notes
- For command observability, JSON mode should include mode metadata (`raw`, `full`, `target_type`) so consumers can interpret payload shape without guessing.
- Keeping text mode and JSON mode as parallel output paths avoids breaking existing operator workflows while enabling automation.
