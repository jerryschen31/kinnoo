# task454 Notes

## Summary
- Updated `kinnoo init` to support framework as a positional argument (for example: `kinnoo init chatgpt my-agent`).
- Added `no-framework` as a supported framework token for barebones initialization paths.
- Updated language option choices/help to align with UAT wording (`python`, `javascript`, `typescript`).
- Added task tests:
  - `tests/test_init.py::test_init_framework_positional_arg`
  - `tests/test_init.py::test_init_no_framework_barebones`

## Files changed
- `src/kinnoo/cli.py`
- `src/kinnoo/init_command.py`
- `tests/test_init.py`
- `TASKS.txt`

## Test run
- Command:
  - `python3 -m pytest tests/test_init.py --testmon -k "test_init_framework_positional_arg or test_init_no_framework_barebones"`
- Result:
  - `2 passed, 51 deselected`

## Teaching notes
- During CLI migrations, keeping a backward-compatible parse fallback for `kinnoo init <agent-name>` can reduce breakage while introducing new positional command contracts.
- Keep framework/language validation centralized in scaffold logic (`init_command.py`) so parser and internal invocations share one source of truth.
