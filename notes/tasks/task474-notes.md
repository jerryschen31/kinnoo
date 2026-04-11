# Task474 - inspect update simplification to 2 arguments

## Summary
- Changed inspect `--update` signature from 3 args to 2 args: `KEY NEW_VALUE`.
- Enabled positional target flexibility so both forms now work:
  - `kinnoo inspect --update runtime.language javascript <target>`
  - `kinnoo inspect <target> --update runtime.language javascript`
- Updated existing inspect update tests to align with the new CLI contract.

## Files changed
- src/kinnoo/cli.py
- tests/test_cli_inspect.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli_inspect.py --testmon -k "test_inspect_update_two_args"
- Result:
  - 1 passed, 16 deselected

## Teaching notes
- Positional/option flexibility is best implemented by letting argparse keep ownership of positional parsing, then validating business constraints (like required target) in dispatch.
- When changing command contracts, update both the parser help text and existing tests to avoid hidden drift between behavior and documentation.
