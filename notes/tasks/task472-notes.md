# Task472 - run replace --sandbox with --enforce-policy

## Summary
- Replaced CLI run flag `--sandbox` with `--enforce-policy`.
- Updated CLI dispatch wiring to use the renamed flag while preserving policy enforcement behavior.
- Updated policy remediation text to guide users with `--enforce-policy` terminology.
- Updated existing run policy tests and added explicit compatibility regression for accepted/rejected flags and help text.

## Files changed
- src/kinnoo/cli.py
- src/kinnoo/sandbox.py
- tests/test_cli.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli.py --testmon -k "test_run_enforce_policy_replaces_sandbox"
- Result:
  - 1 passed, 93 deselected

## Teaching notes
- Flag renames are safest when paired with a parser-level rejection test for the legacy flag and a help-text assertion for the new one.
- Updating remediation strings together with parser changes reduces operator confusion during incident/debug flows.
