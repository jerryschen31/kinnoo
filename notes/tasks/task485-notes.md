# Task485 notes - New kinnoo uninstall command (2026-04-11)

## What changed
- Updated `kinnoo uninstall` parser/help to support:
  - `<name>`
  - `<name>==<version>` (including `latest`)
  - `<archive>.kno==<version>` (including `latest`)
- Implemented uninstall target parsing and mode-specific behavior:
  - directory targets remove installed directory and matching archives
  - archive targets remove only archive versions
- Preserved confirmation prompt flow with `-y/--yes` bypass.

## Files updated
- src/kinnoo/cli.py
- src/kinnoo/uninstall_command.py
- tests/test_cli.py
- TASKS.txt
- TESTS.txt

## Test run
- `python3 -m pytest tests/test_cli.py --testmon -k "uninstall_deletes_agent_directory_and_all_version_archives or uninstall_version_and_latest_alias"`
  - Result: passed

## Teaching notes
- A clear uninstall target grammar is a safety feature: explicit parsing of `<name>` vs `<name>==<version>` vs `<archive>.kno==<version>` reduces accidental deletion blast radius and makes CLI behavior predictable in automation.
