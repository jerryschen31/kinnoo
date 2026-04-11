# Task460 - pack ignore data by default + include/exclude overrides

## Summary
- Added default pack exclusion for top-level data/ paths.
- Added pack CLI options --include and --exclude (repeatable via action=append).
- Implemented include/exclude filtering over selected archive entries and explicit include path expansion.

## Files changed
- src/kinnoo/cli.py
- src/kinnoo/pack_command.py
- tests/test_pack.py
- TASKS.txt

## Tests
- Command:
  - python3 -m pytest tests/test_pack.py --testmon -k "test_pack_excludes_data_by_default or test_pack_include_exclude_options"
- Result:
  - 2 passed, 31 deselected

## Teaching notes
- A safe default for packaging is to exclude high-churn or sensitive directories (like data/) unless explicitly requested.
- The include/exclude model is easiest to reason about when paths are normalized once and matching uses prefix semantics for directory inputs.
- Keep override behavior deterministic: explicit exclude has highest precedence, while include can override default exclusions.
