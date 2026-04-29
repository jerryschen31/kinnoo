# Task468 - install remove deprecated openclaw options

## Summary
- Removed deprecated install CLI options: --state-overwrite, --allow-vulnerable, --ignore-scripts, --openclaw-min-version, and --openclaw-skill.
- Removed corresponding install dispatch handling so those legacy arguments are no longer consumed.
- Added parser regression coverage to assert these options are rejected as unrecognized arguments.

## Files changed
- src/kinnoo/cli.py
- tests/test_cli_install.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli_install.py --testmon -k "test_install_deprecated_options_removed"
- Result:
  - 1 passed, 23 deselected

## Teaching notes
- Removing deprecated arguments at the parser boundary is safer than leaving no-op flags in place because callers fail fast with explicit migration feedback.
- Regression tests for parser contracts should assert behavior from the CLI entrypoint, not internal functions, so user-visible contracts stay protected.
