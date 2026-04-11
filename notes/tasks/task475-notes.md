# Task475 - inspect update confirmation prompt

## Summary
- Updated inspect update prompt to explicit before/after wording:
  - `Changing <key> from <old> to <new>. Proceed? (y/N):`
- Preserved default no/abort behavior when user does not confirm.
- Preserved `--skip-warnings` bypass behavior for non-interactive or scripted updates.
- Added dedicated regression test that covers reject, accept, and bypass flows.

## Files changed
- src/kinnoo/inspect_command.py
- tests/test_cli_inspect.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_cli_inspect.py --testmon -k "test_inspect_update_confirmation_prompt"
- Result:
  - 1 passed, 17 deselected

## Teaching notes
- Prompt wording should include both old and new values to reduce accidental config drift during interactive edits.
- Confirmation defaults (`N`) are a strong safety control for mutation commands; keep bypass flags explicit and opt-in.
