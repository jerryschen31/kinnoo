# Task465 - publish local/remote mutual exclusion

## Summary
- Updated publish CLI parser to enforce mutual exclusion between --local and --remote using argparse's mutually exclusive group.
- Updated help text descriptions:
  - --local: Publish to local registry
  - --remote: Publish to remote registry (default)
- Added targeted parser regression test for invalid combined usage.

## Files changed
- src/kinnoo/cli.py
- tests/test_publish_refactor.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_publish_refactor.py --testmon -k "test_publish_local_remote_mutually_exclusive"
- Result:
  - 1 passed, 4 deselected

## Teaching notes
- Prefer parser-level constraints for mutually exclusive flags because they fail fast and keep downstream command logic simpler.
- Integration tests for CLI contracts should assert both exit code and the parser's explicit conflict diagnostic text.
