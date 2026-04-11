# task455 Notes

## Summary
- Implemented interactive init wizard path for `kinnoo init` when no framework and no agent name are provided in a TTY context.
- Wizard now prompts in sequence:
  - framework selection (numbered list)
  - language selection (only when the selected framework supports multiple languages)
- Added framework-language compatibility matrix updates for task455 requirements.
- Added regression test:
  - `tests/test_init.py::test_init_interactive_wizard`

## Files changed
- `src/kinnoo/init_command.py`
- `src/kinnoo/cli.py`
- `tests/test_init.py`
- `TASKS.txt`

## Test run
- Command:
  - `python3 -m pytest tests/test_init.py --testmon -k test_init_interactive_wizard`
- Result:
  - `1 passed, 53 deselected`

## Teaching notes
- Interactive CLI flows are easiest to test by monkeypatching `sys.argv`, `sys.stdin.isatty()`, and `builtins.input` in-process instead of using subprocesses.
- Keep wizard prompt logic isolated (menu helper functions) so it remains reusable and easier to reason about than embedding prompt branches directly inside command dispatch.
